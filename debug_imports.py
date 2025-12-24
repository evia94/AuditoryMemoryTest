import sys
print(sys.path)
try:
    import gTTS
    print("Imported gTTS")
except ImportError:
    print("Failed gTTS")

try:
    from gTTS import gTTS
    print("Imported from gTTS import gTTS")
except ImportError:
    print("Failed from gTTS import gTTS")

try:
    import gtts
    print("Imported gtts")
except ImportError:
    print("Failed gtts")
