#include <os/user.h>

// Dark theme detection requires calling back into Java/Kotlin via JNI.
// For now, default to false; wire up via JNI in a follow-up.
bool os::user::IsDarkTheme()
{
    return false;
}
