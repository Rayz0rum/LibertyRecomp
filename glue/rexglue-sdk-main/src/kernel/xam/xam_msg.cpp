/**
 ******************************************************************************
 * Xenia : Xbox 360 Emulator Research Project                                 *
 ******************************************************************************
 * Copyright 2022 Ben Vanik. All rights reserved.                             *
 * Released under the BSD license - see LICENSE in the root for more details. *
 ******************************************************************************
 *
 * @modified    Tom Clay, 2026 - Adapted for ReXGlue runtime
 * @modified    2026       - PS4 NP trophy bridge for achievement writes
 * @modified    2026       - Game Center achievement bridge (iOS/macOS)
 */

// Disable warnings about unused parameters for kernel functions
#pragma GCC diagnostic ignored "-Wunused-parameter"

#include <rex/kernel/xam/private.h>
#include <rex/kernel/xboxkrnl/error.h>
#include <rex/logging.h>
#include <rex/ppc/function.h>
#include <rex/ppc/types.h>
#include <rex/system/kernel_state.h>
#include <rex/system/xevent.h>
#include <rex/system/xio.h>
#include <rex/system/xthread.h>
#include <rex/system/xtypes.h>

// ── PS4 trophy bridge ────────────────────────────────────────────────────────
// Forward-declare the bridge entry point so xam_msg.cpp doesn't need to pull
// in any orbis/ headers.  The actual definition lives in os/ps4/achievement_bridge_ps4.cpp
// and is only compiled when LIBERTY_RECOMP_PS4 is defined.
#ifdef LIBERTY_RECOMP_PS4
extern void LibertyPS4OnXboxAchievementUnlocked(uint32_t xbox_id);
#endif

// ── Game Center achievement bridge (iOS / macOS) ─────────────────────────────
// Forward-declared here so this .cpp does not pull in ObjC headers.
// Definition lives in os/gamecenter/achievement_bridge_gc.mm.
#ifdef LIBERTY_RECOMP_GAMECENTER
extern "C" void LibertyGCOnXboxAchievementUnlocked(uint32_t xbox_id);
#endif

// ── XAM message IDs for achievement I/O ─────────────────────────────────────
// app = 0xFB  (XAM user module)
// message 0xB0008 → XamUserWriteAchievements  (write/unlock one achievement)
// The 8-byte buffer layout passed by sub_82A11FB8:
//   [0..3]  be<u32>  user_index  (always 1 for single-user GTA IV)
//   [4..7]  be<u32>  nested_ptr  → guest address of { be<u32> xuid_lo,
//                                                      be<u32> xbox_ach_id }
static constexpr uint32_t kXamApp                 = 0xFB;
static constexpr uint32_t kMsgWriteAchievements   = 0xB0008;

namespace rex {
namespace kernel {
namespace xam {
using namespace rex::system;
using namespace rex::system::xam;

ppc_u32_result_t XMsgInProcessCall_entry(ppc_u32_t app, ppc_u32_t message, ppc_u32_t arg1,
                                         ppc_u32_t arg2) {
  auto result = kernel_state()->app_manager()->DispatchMessageSync(app, message, arg1, arg2);
  if (result == X_ERROR_NOT_FOUND) {
    REXKRNL_ERROR("XMsgInProcessCall: app {:08X} undefined", app);
  }
  return result;
}

ppc_u32_result_t XMsgSystemProcessCall_entry(ppc_u32_t app, ppc_u32_t message, ppc_u32_t buffer,
                                             ppc_u32_t buffer_length) {
  auto result =
      kernel_state()->app_manager()->DispatchMessageAsync(app, message, buffer, buffer_length);
  if (result == X_ERROR_NOT_FOUND) {
    REXKRNL_ERROR("XMsgSystemProcessCall: app {:08X} undefined", app);
  }
  return result;
}

struct XMSGSTARTIOREQUEST_UNKNOWNARG {
  be<uint32_t> unk_0;
  be<uint32_t> unk_1;
};

// ── xeXMsgStartIORequestEx ───────────────────────────────────────────────────
//
// Central intercept point.  On PS4 / iOS / macOS builds we intercept the
// achievement-write message (app=0xFB, msg=0xB0008) before normal dispatch:
//   1. Extract the Xbox achievement ID from the guest buffer.
//   2. Forward to the platform trophy/achievement bridge:
//        PS4  → sceNpTrophyUnlockTrophy + auto-platinum scan
//        iOS/macOS → GKAchievement reportAchievements + auto-platinum scan
//   3. Complete the overlapped with SUCCESS and return IO_PENDING so the game
//      thread unblocks normally (otherwise the worker gets error 1627).
//
// All other messages fall through to the normal DispatchMessageAsync path.

X_HRESULT xeXMsgStartIORequestEx(uint32_t app, uint32_t message, uint32_t overlapped_ptr,
                                 uint32_t buffer_ptr, uint32_t buffer_length,
                                 XMSGSTARTIOREQUEST_UNKNOWNARG* unknown) {

#ifdef LIBERTY_RECOMP_PS4
  // ── Achievement write intercept ─────────────────────────────────────────
  if (app == kXamApp && message == kMsgWriteAchievements && buffer_ptr &&
      buffer_length >= 8) {
    // The 8-byte buffer is big-endian guest memory.
    // [0] = user_index, [1] = nested guest ptr → {xuid_lo, xbox_ach_id}
    auto* hbuf = kernel_state()->memory()->TranslateVirtual<be<uint32_t>*>(buffer_ptr);
    const uint32_t nested_gptr = hbuf[1];  // auto byte-swapped by be<>

    if (nested_gptr) {
      auto* nested = kernel_state()->memory()->TranslateVirtual<be<uint32_t>*>(nested_gptr);
      // nested[0] = xuid_lo, nested[1] = xbox achievement ID (1-indexed)
      const uint32_t xbox_id = nested[1];  // auto byte-swapped by be<>

      REXKRNL_DEBUG("XMsgStartIORequest: PS4 bridge — xbox_achievement_id={}", xbox_id);
      LibertyPS4OnXboxAchievementUnlocked(xbox_id);
    }

    // Complete the overlapped with SUCCESS so the worker thread unblocks.
    // Returning IO_PENDING is what the game expects when an overlapped is set.
    if (overlapped_ptr) {
      kernel_state()->CompleteOverlappedImmediate(overlapped_ptr, X_ERROR_SUCCESS);
      return X_ERROR_IO_PENDING;
    }
    return X_ERROR_SUCCESS;
  }
#elif defined(LIBERTY_RECOMP_GAMECENTER)
  // ── Game Center achievement write intercept ──────────────────────────────
  if (app == kXamApp && message == kMsgWriteAchievements && buffer_ptr &&
      buffer_length >= 8) {
    auto* hbuf = kernel_state()->memory()->TranslateVirtual<be<uint32_t>*>(buffer_ptr);
    const uint32_t nested_gptr = hbuf[1];

    if (nested_gptr) {
      auto* nested = kernel_state()->memory()->TranslateVirtual<be<uint32_t>*>(nested_gptr);
      const uint32_t xbox_id = nested[1];

      REXKRNL_DEBUG("XMsgStartIORequest: GC bridge — xbox_achievement_id={}", xbox_id);
      LibertyGCOnXboxAchievementUnlocked(xbox_id);
    }

    if (overlapped_ptr) {
      kernel_state()->CompleteOverlappedImmediate(overlapped_ptr, X_ERROR_SUCCESS);
      return X_ERROR_IO_PENDING;
    }
    return X_ERROR_SUCCESS;
  }
#endif  // LIBERTY_RECOMP_PS4 / LIBERTY_RECOMP_GAMECENTER

  // ── Default dispatch ─────────────────────────────────────────────────────
  auto result =
      kernel_state()->app_manager()->DispatchMessageAsync(app, message, buffer_ptr, buffer_length);
  if (result == X_E_NOTFOUND) {
    REXKRNL_ERROR("XMsgStartIORequestEx: app {:08X} undefined", app);
    result = X_E_INVALIDARG;
    XThread::SetLastError(X_ERROR_NOT_FOUND);
  }
  if (overlapped_ptr) {
    kernel_state()->CompleteOverlappedImmediate(overlapped_ptr, result);
    result = X_ERROR_IO_PENDING;
  }
  if (result == X_ERROR_SUCCESS || result == X_ERROR_IO_PENDING) {
    XThread::SetLastError(0);
  }
  return result;
}

ppc_u32_result_t XMsgStartIORequestEx_entry(ppc_u32_t app, ppc_u32_t message,
                                            ppc_ptr_t<XAM_OVERLAPPED> overlapped_ptr,
                                            ppc_u32_t buffer_ptr, ppc_u32_t buffer_length,
                                            ppc_ptr_t<XMSGSTARTIOREQUEST_UNKNOWNARG> unknown_ptr) {
  return xeXMsgStartIORequestEx(app, message, overlapped_ptr.guest_address(), buffer_ptr,
                                buffer_length, unknown_ptr);
}

ppc_u32_result_t XMsgStartIORequest_entry(ppc_u32_t app, ppc_u32_t message,
                                          ppc_ptr_t<XAM_OVERLAPPED> overlapped_ptr,
                                          ppc_u32_t buffer_ptr, ppc_u32_t buffer_length) {
  return xeXMsgStartIORequestEx(app, message, overlapped_ptr.guest_address(), buffer_ptr,
                                buffer_length, nullptr);
}

ppc_u32_result_t XMsgCancelIORequest_entry(ppc_ptr_t<XAM_OVERLAPPED> overlapped_ptr,
                                           ppc_u32_t wait) {
  X_HANDLE event_handle = XOverlappedGetEvent(overlapped_ptr);
  if (event_handle && wait) {
    auto ev = kernel_state()->object_table()->LookupObject<XEvent>(event_handle);
    if (ev) {
      ev->Wait(0, 0, true, nullptr);
    }
  }

  return 0;
}

ppc_u32_result_t XMsgCompleteIORequest_entry(ppc_ptr_t<XAM_OVERLAPPED> overlapped_ptr,
                                             ppc_u32_t result, ppc_u32_t extended_error,
                                             ppc_u32_t length) {
  kernel_state()->CompleteOverlappedImmediateEx(overlapped_ptr.guest_address(), result,
                                                extended_error, length);
  return X_ERROR_SUCCESS;
}

ppc_u32_result_t XamGetOverlappedResult_entry(ppc_ptr_t<XAM_OVERLAPPED> overlapped_ptr,
                                              ppc_pu32_t length_ptr, ppc_u32_t unknown) {
  uint32_t result;
  if (overlapped_ptr->result != X_ERROR_IO_PENDING) {
    result = overlapped_ptr->result;
  } else if (!overlapped_ptr->event) {
    result = X_ERROR_IO_INCOMPLETE;
  } else {
    auto ev = kernel_state()->object_table()->LookupObject<XEvent>(overlapped_ptr->event);
    result = ev->Wait(3, 1, 0, nullptr);
    if (XSUCCEEDED(result)) {
      result = overlapped_ptr->result;
    } else {
      result = xboxkrnl::xeRtlNtStatusToDosError(result);
    }
  }
  if (XSUCCEEDED(result) && length_ptr) {
    *length_ptr = overlapped_ptr->length;
  }
  return result;
}

}  // namespace xam
}  // namespace kernel
}  // namespace rex

XAM_EXPORT(__imp__XMsgInProcessCall, rex::kernel::xam::XMsgInProcessCall_entry)
XAM_EXPORT(__imp__XMsgSystemProcessCall, rex::kernel::xam::XMsgSystemProcessCall_entry)
XAM_EXPORT(__imp__XMsgStartIORequestEx, rex::kernel::xam::XMsgStartIORequestEx_entry)
XAM_EXPORT(__imp__XMsgStartIORequest, rex::kernel::xam::XMsgStartIORequest_entry)
XAM_EXPORT(__imp__XMsgCancelIORequest, rex::kernel::xam::XMsgCancelIORequest_entry)
XAM_EXPORT(__imp__XMsgCompleteIORequest, rex::kernel::xam::XMsgCompleteIORequest_entry)
XAM_EXPORT(__imp__XamGetOverlappedResult, rex::kernel::xam::XamGetOverlappedResult_entry)

XAM_EXPORT_STUB(__imp__XMsgAcquireAsyncMessageFromOverlapped);
XAM_EXPORT_STUB(__imp__XMsgProcessRequest);
XAM_EXPORT_STUB(__imp__XMsgReleaseAsyncMessageToOverlapped);
