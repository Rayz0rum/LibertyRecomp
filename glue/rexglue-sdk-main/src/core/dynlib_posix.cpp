#include <rex/platform.h>
#include <rex/platform/dynlib.h>

static_assert(REX_PLATFORM_POSIX, "This file requires a POSIX-like platform (macOS, iOS, Linux, Android, PS4, Switch)");

// Switch (libnx) is a statically-linked homebrew environment — there is no
// dynamic linker and no dlopen/dlsym. All code is compiled into the NRO at
// build time. DynamicLibrary operations are therefore no-ops on Switch.
//
// PS4 (OpenOrbis) does support dynamic modules via sceKernelLoadStartModule and
// sceKernelDlsym. The standard POSIX dlopen()/dlsym() wrappers provided by the
// OpenOrbis toolchain delegate to these SCE calls, so we use them directly and
// they work. The only exception is dlsym() symbol lookup which uses integer
// handles, not void* opaque handles — but the OpenOrbis libc shim handles that.
#if !REX_PLATFORM_SWITCH
#include <dlfcn.h>
#endif

namespace rex::platform {

DynamicLibrary::~DynamicLibrary() {
  Close();
}

DynamicLibrary::DynamicLibrary(DynamicLibrary&& other) noexcept : handle_(other.handle_) {
  other.handle_ = nullptr;
}

DynamicLibrary& DynamicLibrary::operator=(DynamicLibrary&& other) noexcept {
  if (this != &other) {
    Close();
    handle_ = other.handle_;
    other.handle_ = nullptr;
  }
  return *this;
}

bool DynamicLibrary::Load(const std::filesystem::path& path) {
  Close();
#if REX_PLATFORM_SWITCH
  // No dynamic loading on Switch; all libraries are statically linked.
  (void)path;
  return false;
#else
  handle_ = dlopen(path.c_str(), RTLD_LAZY);
  return handle_ != nullptr;
#endif
}

void DynamicLibrary::Close() {
  if (handle_) {
#if !REX_PLATFORM_SWITCH
    dlclose(handle_);
#endif
    handle_ = nullptr;
  }
}

void* DynamicLibrary::GetRawSymbol(const char* name) const {
  if (!handle_)
    return nullptr;
#if REX_PLATFORM_SWITCH
  // No dynamic symbol lookup on Switch.
  (void)name;
  return nullptr;
#else
  return dlsym(handle_, name);
#endif
}

}  // namespace rex::platform
