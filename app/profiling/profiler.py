import pandas as pd


class DataProfiler:

    @staticmethod
    def profile_dataframe(
        dataframe: pd.DataFrame
    ) -> dict:

        numeric_columns = dataframe.select_dtypes(
            include=["number"]
        ).columns.tolist()

        categorical_columns = dataframe.select_dtypes(
            include=["object"]
        ).columns.tolist()

        datetime_columns = dataframe.select_dtypes(
            include=["datetime64"]
        ).columns.tolist()

        missing_values = {
            column: int(
                dataframe[column].isnull().sum()
            )
            for column in dataframe.columns
        }

        return {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "column_names": dataframe.columns.tolist(),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
            "missing_values": missing_values
        }

