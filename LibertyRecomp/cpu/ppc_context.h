#pragma once
// gta4_config.h must be included before context.h so PPC_LOOKUP_FUNC
// and PPC_CALL_INDIRECT_FUNC resolve to the real function table macros.
#include "gta4_config.h"

// RexGlue's PPC types are authoritative.
#include <rex/ppc/context.h>
#include <rex/ppc/function.h>

inline PPCContext* GetPPCContext()
{
    return rex::g_current_ppc_context;
}

inline void SetPPCContext(PPCContext& ctx)
{
    rex::g_current_ppc_context = &ctx;
}
