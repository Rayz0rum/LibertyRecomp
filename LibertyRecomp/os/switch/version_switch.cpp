#include <os/version.h>
#include <switch.h>

os::version::OSVersion os::version::GetOSVersion()
{
    SetSysFirmwareVersion fw{};
    if (R_SUCCEEDED(setsysGetFirmwareVersion(&fw)))
        return { static_cast<uint32_t>(fw.major),
                 static_cast<uint32_t>(fw.minor),
                 static_cast<uint32_t>(fw.micro) };
    return { 0, 0, 0 };
}
