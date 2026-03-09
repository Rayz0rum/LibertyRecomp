#include <os/media.h>
// AudioManager.isMusicActive() requires JNI; stub for now.
bool os::media::IsExternalMediaPlaying()
{
    return false;
}
