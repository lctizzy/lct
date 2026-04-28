import whisper
import warnings
warnings.filterwarnings('ignore')

print('Loading Whisper small model...')
model = whisper.load_model('small')

print('Transcribing video...')
result = model.transcribe(
    r'C:\Users\liche\Desktop\tiktok_7609673482208627988 (1).mp4',
    language='en',
    task='transcribe',
    condition_on_previous_text=False,
    compression_ratio_threshold=2.4,
    no_speech_threshold=0.6,
    verbose=True
)

print('\n' + '='*60)
print('WHISPER TRANSCRIPTION:')
print('='*60)
print(result['text'])
print('\n' + '='*60)
print('SEGMENTS:')
for seg in result['segments']:
    start = seg['start']
    end = seg['end']
    text = seg['text']
    print(f"[{start:.1f}s - {end:.1f}s] {text}")
