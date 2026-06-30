import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from scipy import stats

class HCHOHotspotDetector:
    """
    Identifies HCHO hotspots using:
    1. Statistical Z-score thresholding (>1.5σ = potential hotspot)
    2. DBSCAN spatial clustering
    """
    def __init__(self, z_threshold=1.5, dbscan_eps=0.5, dbscan_min_samples=3):
        self.z_threshold = z_threshold
        self.eps = dbscan_eps
        self.min_samples = dbscan_min_samples

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Calculate Z-score
        df['z_score'] = stats.zscore(df['hcho_value'], nan_policy='omit')
        df['is_anomaly'] = df['z_score'] > self.z_threshold
        
        df['anomaly_magnitude'] = np.where(
            df['is_anomaly'], 
            df['hcho_value'] - df['hcho_value'].mean(), 
            0
        )
        return df

    def cluster_hotspots(self, anomaly_df: pd.DataFrame):
        anomalies = anomaly_df[anomaly_df['is_anomaly']].copy()
        if len(anomalies) < self.min_samples:
            return anomalies, pd.DataFrame()

        coords = anomalies[['lat', 'lon']].values
        
        # DBSCAN clustering (using ball_tree & haversine metric requires radians)
        db = DBSCAN(
            eps=np.radians(self.eps),
            min_samples=self.min_samples,
            algorithm='ball_tree',
            metric='haversine'
        )
        labels = db.fit_predict(np.radians(coords))
        
        anomalies['cluster_id'] = labels
        anomalies['is_hotspot'] = labels >= 0
        
        hotspot_stats = anomalies[anomalies['is_hotspot']].groupby('cluster_id').agg(
            center_lat=('lat', 'mean'),
            center_lon=('lon', 'mean'),
            mean_hcho=('hcho_value', 'mean'),
            max_hcho=('hcho_value', 'max'),
            point_count=('hcho_value', 'count'),
            mean_zscore=('z_score', 'mean')
        ).reset_index()

        # Simple classification
        hotspot_stats['intensity'] = pd.cut(
            hotspot_stats['mean_zscore'],
            bins=[1.5, 2.5, 3.5, float('inf')],
            labels=['moderate', 'high', 'extreme']
        )
        
        return anomalies, hotspot_stats
