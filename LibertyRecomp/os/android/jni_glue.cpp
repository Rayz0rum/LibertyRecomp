// JNI glue — called from LibertySDLActivity.java before SDL starts
// Sets paths that the native process layer reads.
#include <jni.h>
#include <string>
#include <cstring>
#include <malloc.h>

const char* g_androidAppInternalPath = nullptr;
const char* g_androidObbPath         = nullptr;

extern "C" JNIEXPORT void JNICALL
Java_com_libertyrecomp_LibertySDLActivity_nativeSetPaths(
    JNIEnv* env,
    jclass  /*clazz*/,
    jstring internalPath,
    jstring obbPath)
{
    auto copyJString = [&](jstring js) -> const char* {
        if (!js) return nullptr;
        const char* tmp = env->GetStringUTFChars(js, nullptr);
        size_t len = strlen(tmp);
        char* buf = static_cast<char*>(malloc(len + 1));
        memcpy(buf, tmp, len + 1);
        env->ReleaseStringUTFChars(js, tmp);
        return buf;
    };

    free(const_cast<char*>(g_androidAppInternalPath));
    free(const_cast<char*>(g_androidObbPath));

    g_androidAppInternalPath = copyJString(internalPath);
    g_androidObbPath         = copyJString(obbPath);
}
