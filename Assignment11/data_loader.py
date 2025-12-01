import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

ASSIGNMENT_ROOT = Path(__file__).resolve().parent
DATA_DIR = ASSIGNMENT_ROOT / "data"


@dataclass
class LoadedData:
    """
    a dataclass for market data.
    """
    market_data: pd.DataFrame
    tickers: List[str]
    features_config: Dict
    model_params: Dict


class DataLoader:
    """
    Centralizes loading of market data, tickers, and configuration files.
    """

    def __init__(self, data_dir: Path | str = DATA_DIR) -> None:
        self.data_dir = Path(data_dir)

    def _read_json(self, filename: str) -> Dict:
        """
        read the json

        Args:
            filename (str): path to json file to be opened

        Returns:
            Dict: json formatted as dictionary
        """
        path = self.data_dir / filename
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_market_data(self) -> pd.DataFrame:
        """
        
        Loads market data from csv for model usage

        Returns:
            pd.DataFrame: market dataframe to be loaded 
            from market_data_ml.csv
        """
        
        # get path, sort the values by ticker and date in the csv
        path = self.data_dir / "market_data_ml.csv"
        df = pd.read_csv(path, parse_dates=["date"])
        df.sort_values(["ticker", "date"], inplace=True)
        
        # reset the index and return the dataframe
        df.reset_index(drop=True, inplace=True)
        return df

    def load_tickers(self) -> List[str]:
        """
        Loads tickers from csv file that was given

        Returns:
            List[str]: a list of tickers sorted alphabetically
        """
        
        # read the csv and get only unique tickers in list data structure
        path = self.data_dir / "tickers-1.csv"
        tickers_df = pd.read_csv(path)
        tickers = tickers_df["symbol"].dropna().unique().tolist()
        return sorted(tickers)

    def load_features_config(self) -> Dict:
        return self._read_json("features_config.json")

    def load_model_params(self) -> Dict:
        """
        
        Loads the model parameters from the given json
        for the assignment

        Returns:
            Dict: dictionary of model parameters from model_params.json
        """
        return self._read_json("model_params.json")

    def load_all(self) -> LoadedData:
        """
        
        Loads all the data coherently using the above functions

        Raises:
            ValueError: if there's any missing tickers in the dataset

        Returns:
            LoadedData: a Loaded Data Object with each attribute being a necessary work
        """
        
        # load all the different data necessary
        data = self.load_market_data()
        tickers = self.load_tickers()
        features_config = self.load_features_config()
        model_params = self.load_model_params()
        
        # ensure that we have tickers that align, and we haven't left one out
        missing = set(tickers) - set(data["ticker"].unique())
        if missing:
            raise ValueError(f"Missing tickers in dataset: {', '.join(sorted(missing))}")

        # return loaded data object
        return LoadedData(
            market_data=data,
            tickers=tickers,
            features_config=features_config,
            model_params=model_params,
        )


__all__ = ["DataLoader", "LoadedData"]
