import faster_whisper as fw

model = fw.WhisperModel('base',device='gpu',compute_type='int8')