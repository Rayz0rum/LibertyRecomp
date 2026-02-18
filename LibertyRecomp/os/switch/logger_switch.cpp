// Switch logger — uses nxlink stdout or svcOutputDebugString
#include <os/logger.h>
#include <switch.h>
#include <cstdio>
#include <string>

void os::logger::Init()
{
    // nxlinkStdio() should be called by the main entry point if nxlink debugging is desired.
    // Here we just confirm initialization via debug output.
    svcOutputDebugString("LibertyRecomp: logger init\n", 27);
}

void os::logger::Log(const std::string_view str, ELogType type, const char* func)
{
    std::string msg;
    if (func)
        msg = std::string("[") + func + "] " + std::string(str) + "\n";
    else
        msg = std::string(str) + "\n";

    // svcOutputDebugString goes to Atmosphere's sysmodule log
    svcOutputDebugString(msg.c_str(), static_cast<u64>(msg.size()));
    // Also print so nxlink / Goldleaf console can see it
    printf("%s", msg.c_str());
}
