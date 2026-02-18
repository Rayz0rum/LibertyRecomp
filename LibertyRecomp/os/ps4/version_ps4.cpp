#include <os/version.h>
#include <orbis/libkernel.h>

os::version::OSVersion os::version::GetOSVersion()
{
    OrbisKernelSwVersion ver{};
    sceKernelGetSystemSwVersion(&ver);
    // Version string like "09.00"
    uint32_t major = 0, minor = 0;
    sscanf(ver.versionString, "%u.%u", &major, &minor);
    return { major, minor, 0 };
}
