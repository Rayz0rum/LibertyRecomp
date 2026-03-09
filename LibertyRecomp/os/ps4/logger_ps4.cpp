// PS4 logger — uses OpenOrbis kernel debug print
#include <os/logger.h>
#include <orbis/libkernel.h>
#include <stdio.h>
#include <string>

void os::logger::Init()
{
    // sceKernelDebugOutText is available under Mira/OpenOrbis jailbreak environment
    sceKernelDebugOutText(0, "LibertyRecomp: logger initialized\n");
}

void os::logger::Log(const std::string_view str, ELogType type, const char* func)
{
    std::string msg;
    if (func)
        msg = std::string("[") + func + "] " + std::string(str) + "\n";
    else
        msg = std::string(str) + "\n";

    sceKernelDebugOutText(0, msg.c_str());
    // Also print to fd 1 (stdout goes to OpenOrbis debug sink)
    printf("%s", msg.c_str());
}
