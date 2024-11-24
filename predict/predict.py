import json
from prophet import Prophet
import numpy as np
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
import pandas as pd
from sklearn.pipeline import make_pipeline


print("NumPy version:", np.__version__)
print("Pandas version:", pd.__version__)





def getPrediction(Dataset):

    predictDatasets = []

    for dataset in Dataset:


        predictDataset = []

        df = pd.read_csv(f'{dataset}.csv')

        #clearDate
        df.drop(df.columns[0], axis=1, inplace=True)
        df.drop(df.columns[1], axis=1, inplace=True)
        df = df.groupby('Country/Region').sum().reset_index()
        df.drop('Long', axis=1, inplace=True)
        df=df.T
        df = df.drop(df.index[0])
        df=df.tail(400)
        #Time
        dateTime = pd.DataFrame(df.index[0:].values, columns=['ds'])
        dateTime['ds'] = pd.to_datetime(dateTime['ds'], errors='coerce')

        #predproccesing

        imputerNum = SimpleImputer(missing_values=np.nan, strategy='mean')
        prepipeline = make_pipeline(imputerNum)
        preColumnsTransaport = make_column_transformer(
            (prepipeline, df.columns.tolist())
        )
        transformed_data = preColumnsTransaport.fit_transform(df)
        df = pd.DataFrame(transformed_data)

        for i in df:

            stateData = pd.DataFrame(df.iloc[:, 0])
            result_df = pd.concat([dateTime, stateData], axis=1)
            result_df.columns = ['ds', 'y']

            model = Prophet(changepoint_prior_scale=0.05, seasonality_prior_scale=10)
            model.fit(result_df)

            # Predpoveď na budúce dátumy
            future = model.make_future_dataframe( periods=40)
            forecast = model.predict(future)
            last_50_rows_last_column = forecast.iloc[-50:, -1]
            predictDataset.append(last_50_rows_last_column.tolist())
        predictDatasets.append(predictDataset)

    return json.dumps(predictDatasets)










prediction_data=getPrediction(['confirmed_case'])

























