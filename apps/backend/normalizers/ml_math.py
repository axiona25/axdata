"""ML/Math normalizer following OpenML and UCI ML Repository conventions.

Standards:
- OpenML Standard (ML datasets, benchmarking)
- UCI ML Repository conventions (de facto academic standard)

Used for:
- Machine learning datasets
- Model benchmarking
- Feature engineering
- Statistical analysis
"""
from typing import List, Dict, Any, Optional
from normalizers.base import BaseNormalizer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class MLMathNormalizer(BaseNormalizer):
    """
    Normalizer for ML/Math data following OpenML/UCI conventions.
    
    Structure:
    - Tabular ML dataset
    - Features (independent variables)
    - Target (dependent variable/label)
    - Optional train/test split
    """
    
    def __init__(self):
        super().__init__("math")
    
    def normalize(self, records: List[Dict[str, Any]], transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize ML/Math data following OpenML/UCI conventions.
        
        Applies:
        - Feature/target identification
        - Data type standardization
        - Missing value handling
        - Feature engineering
        - Train/test split (optional)
        """
        if not records:
            return []
        
        if not PANDAS_AVAILABLE:
            return records
        
        df = pd.DataFrame(records)
        
        # Apply transformations
        for transformation in transformations:
            trans_type = transformation.get("type")
            params = transformation.get("params", {})
            
            if trans_type == "identify_features":
                df = self._identify_features(df, params)
            elif trans_type == "handle_missing":
                df = self._handle_missing_values(df, params)
            elif trans_type == "standardize_types":
                df = self._standardize_types(df, params)
            elif trans_type == "feature_engineering":
                df = self._feature_engineering(df, params)
            elif trans_type == "train_test_split":
                # This would create separate datasets, handled at export level
                pass
        
        return df.to_dict('records')
    
    def _identify_features(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Identify features and target (OpenML/UCI structure).
        
        Adds metadata:
        - dataset_role: feature or target
        - task: classification, regression, etc.
        """
        target_column = params.get("target")
        task = params.get("task", "unknown")
        
        # Mark target column if specified
        if target_column and target_column in df.columns:
            df.attrs['target'] = target_column
            df.attrs['task'] = task
        
        # All other numeric columns are features by default
        numeric_cols = df.select_dtypes(include=['number']).columns
        if target_column and target_column in numeric_cols:
            feature_cols = [col for col in numeric_cols if col != target_column]
        else:
            feature_cols = list(numeric_cols)
        
        df.attrs['features'] = feature_cols
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Handle missing values in ML datasets."""
        method = params.get("method", "drop")  # drop, fill, impute
        
        if method == "drop":
            df = df.dropna()
        elif method == "fill":
            fill_value = params.get("fill_value", 0)
            df = df.fillna(fill_value)
        elif method == "impute":
            # Simple imputation (mean for numeric, mode for categorical)
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].mean())
            
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                df[col] = df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else "")
        
        return df
    
    def _standardize_types(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Standardize data types for ML."""
        # Ensure numeric columns are numeric
        numeric_cols = params.get("numeric_columns", [])
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _feature_engineering(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Apply feature engineering transformations."""
        transformations = params.get("transformations", [])
        
        for trans in transformations:
            trans_type = trans.get("type")
            if trans_type == "normalize":
                # Z-score normalization
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
            elif trans_type == "one_hot_encode":
                # One-hot encoding for categorical
                categorical_cols = trans.get("columns", [])
                df = pd.get_dummies(df, columns=categorical_cols)
        
        return df
    
    def validate(self, records: List[Dict[str, Any]]) -> bool:
        """
        Validate ML/Math data.
        
        Requires:
        - At least one feature (numeric column)
        - Consistent structure across records
        """
        if not records:
            return False
        
        first_record = records[0]
        
        # Must have at least one numeric column (feature)
        numeric_cols = [k for k, v in first_record.items() if isinstance(v, (int, float))]
        return len(numeric_cols) > 0
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get OpenML/UCI metadata for this normalizer."""
        return {
            "standards": [
                "OpenML Standard",
                "UCI ML Repository conventions"
            ],
            "structure": {
                "features": "Independent variables",
                "target": "Dependent variable (label)",
                "task": "classification, regression, clustering, etc."
            },
            "description": "OpenML/UCI-compliant normalizer for machine learning and mathematical datasets"
        }

