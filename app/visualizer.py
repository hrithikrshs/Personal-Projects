import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa.display
import numpy as np
import io
import base64

plt.style.use('seaborn-v0_8-darkgrid')

def create_spectrogram_plot(D, sr):
    try:
        fig, ax = plt.subplots(figsize=(12,8))
        fig.patch.set_facecolor('#1a1a1a')
        img = librosa.display.specshow(D, y_axis='log', sr=sr, hop_length=512, x_axis='time', ax=ax, cmap='plasma')
        ax.set_title('Audio Spectrogram', color='w')
        ax.tick_params(colors='w')
        cbar = fig.colorbar(img, ax=ax, format='%+2.0f dB')
        cbar.ax.tick_params(colors='w')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#1a1a1a', bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return {'success': True, 'image': img_b64}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_nmf_components_plot(W, H):
    try:
        n = W.shape[1]
        fig, axs = plt.subplots(n, 2, figsize=(14, n*2.5))
        fig.patch.set_facecolor('#1a1a1a')
        if n == 1: axs = axs.reshape(1,-1)
        for i in range(n):
            axs[i,0].plot(W[:,i], color='#00d4ff')
            axs[i,1].plot(H[i], color='#00ff88')
            for j in (0,1):
                axs[i,j].tick_params(colors='w', labelsize=8)
                axs[i,j].set_facecolor('#2d2d2d')
        axs[0,0].set_title('Frequency Spectra (W)', color='w')
        axs[0,1].set_title('Temporal Activations (H)', color='w')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#1a1a1a', bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return {'success': True, 'image': img_b64}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_cluster_plot(labels):
    try:
        fig, ax = plt.subplots(figsize=(12,6))
        fig.patch.set_facecolor('#1a1a1a')
        ax.scatter(np.arange(len(labels)), labels, c=labels, cmap='viridis')
        ax.set_title('K-Means Clustering', color='w')
        ax.set_xlabel('Segment Index')
        ax.set_ylabel('Cluster')
        ax.tick_params(colors='w')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#1a1a1a', bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return {'success': True, 'image': img_b64}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_summary_plot(results):
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.patch.set_facecolor('#1a1a1a')
        cluster_counts = [results['cluster_0_count'], results['cluster_1_count']]
        colors = ['#00d4ff', '#00ff88']

        ax1.set_facecolor('#2d2d2d')
        bars = ax1.bar(['Heart Sounds', 'Lung Sounds'], cluster_counts, color=colors, alpha=0.8)
        ax1.set_title('Sound Classification Distribution', color='white', fontsize=12)
        ax1.set_ylabel('Number of Segments', color='white')
        ax1.tick_params(colors='white')
        for bar, count in zip(bars, cluster_counts):
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{count}', ha='center', va='bottom', color='white')

        ax2.set_facecolor('#2d2d2d')
        params = ['Components', 'Sample Rate (kHz)', 'Duration (s)']
        values = [results['n_components'], results['sr']/1000, results['duration']]
        bars2 = ax2.bar(params, values, color=['#ff6b6b', '#4ecdc4', '#45b7d1'], alpha=0.8)
        ax2.set_title('Audio Processing Parameters', color='white', fontsize=12)
        ax2.tick_params(colors='white')
        for bar, value in zip(bars2, values):
            ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{value:.1f}', ha='center', va='bottom', color='white')

        ax3.set_facecolor('#2d2d2d')
        ratios = [results['cluster_ratio'], 1 - results['cluster_ratio']]
        labels_pie = ['Heart Sounds', 'Lung Sounds']
        wedges, texts, autotexts = ax3.pie(ratios, labels=labels_pie, colors=colors, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Sound Type Distribution', color='white', fontsize=12)
        for text in texts:
            text.set_color('white')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax4.set_facecolor('#2d2d2d')
        matrix_info = [
            f"W Matrix: {results['W_shape'][0]} × {results['W_shape'][1]}",
            f"H Matrix: {results['H_shape']} × {results['H_shape'][1]}",
            f"Spectrogram: {results['D_shape']} × {results['D_shape'][1]}"
        ]
        ax4.text(0.1, 0.7, 'Matrix Dimensions:', fontsize=14, color='white', fontweight='bold')
        for i, info in enumerate(matrix_info):
            ax4.text(0.1, 0.5 - i*0.15, info, fontsize=11, color='white')
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#1a1a1a', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return {'success': True, 'image': img_b64}
    except Exception as e:
        return {'success': False, 'error': str(e)}
