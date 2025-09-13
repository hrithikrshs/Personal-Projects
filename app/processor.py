import numpy as np
import librosa
from sklearn.cluster import KMeans

def process_audio(file_path, n_components=8, max_iter=5000, sr=16000):
    try:
        y, sr_loaded = librosa.load(file_path, sr=sr)
        stft = librosa.stft(y, n_fft=1024, hop_length=512)
        magnitude, _ = librosa.magphase(stft)
        D = librosa.amplitude_to_db(magnitude, ref=np.max)
        mag = magnitude + 1e-10
        rows, cols = mag.shape

        W = np.abs(np.random.normal(0, 2.5, size=(rows, n_components)))
        H = np.abs(np.random.normal(0, 2.5, size=(n_components, cols)))

        for _ in range(max_iter):
            H *= (W.T @ (mag / (W @ H + 1e-10))) / (W.T @ np.ones((rows, cols)) + 1e-10)
            W *= ((mag / (W @ H + 1e-10)) @ H.T) / (np.ones((rows, cols)) @ H.T + 1e-10)

        labels = KMeans(n_clusters=2, random_state=0, n_init=10).fit_predict(H.T)

        results = {
            'sr': sr_loaded,
            'duration': len(y)/sr_loaded,
            'n_components': n_components,
            'max_iter': max_iter,
            'W_shape': W.shape,
            'H_shape': H.shape,
            'D_shape': D.shape,
            'cluster_0_count': int(np.sum(labels == 0)),
            'cluster_1_count': int(np.sum(labels == 1)),
            'cluster_ratio': float(np.mean(labels == 0))
        }

        return {
            'success': True,
            'sr': sr_loaded,
            'W': W,
            'H': H,
            'D': D,
            'labels': labels,
            'results': results
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_audio_info(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        duration = len(y) / sr
        return {
            'success': True,
            'sample_rate': sr,
            'duration': duration,
            'samples': len(y),
            'channels': 1  # librosa loads mono by default
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
