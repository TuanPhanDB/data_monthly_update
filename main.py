def automation():
#   from google.colab import drive
#   drive.mount('/content/drive')

  #----------------------------------------------------------------------------------------------------#
  #-------------------------------Import necessary libraries-------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  import pandas as pd
  import datetime as dt
  from datetime import date
  import numpy as np
  import os
  import glob
  import requests
  from io import StringIO
  import validators

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Function to retrieve data from API-------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  def get_from_oecd(query):
      if "?" in query:
          return pd.read_csv(
              f"{query}&format=csv"
          )
      else:
          return pd.read_csv(
              f"{query}?format=csv"
          )

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Access to file in GitHub-----------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  # define parameters for a request
  
  token = os.environ["token"]
  owner = 'GARInstitute'
  repo = 'full-data-monthly-update'
  path = 'Relevant_variables.csv'

  # send a request
  r = requests.get(
    'https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(
    owner=owner, repo=repo, path=path),
    headers={
        'accept': 'application/vnd.github.v3.raw',
        'authorization': 'token {}'.format(token)
            }
    )

  # convert string to StringIO object
  string_io_obj = StringIO(r.text)

  # Load data to df
  df = pd.read_csv(string_io_obj)

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Create dataframe-------------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  #take row that have valid API
  API_notnull = pd.notnull(df.API)
  valid_url = df["API"].apply(validators.url)
  df = df[API_notnull & valid_url]

  #display error APIs
  invalid_url = ~df["API"].apply(validators.url)

  #export invalid file
  name = 'invalid_APIs.xlsx'
  df[invalid_url].to_excel(name)

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Create final dataframe-------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  end = date.today()
  range_date = pd.date_range(start ='1/2010', end=end, freq ='M')
  range_date = range_date.to_period('M')
  full_df = pd.DataFrame(data=range_date, columns=['TIME_PERIOD'])

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Fossil df function-----------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  def fossil_df(df, full_df):
    #create fossil fuel support dataframe
    #fossil_df = df[156:]
    fossil_df = df[df['Dataset'].str.contains('Fossil Fuel Support ')] 
    msg = ''
    #go through every dataset
    for index, row in fossil_df.iterrows():

      #get data from API column
      try:
        data = get_from_oecd(row['API'])

        #drop rows that have NaN in 'OBS_VALUE'
        data = data.dropna(subset=['OBS_VALUE'])

        #go through every row in current dataset
        for idx, cur_row in data.iterrows():

          #create new column's name for fossil_full
          name = row['Dataset'] + '[' + cur_row['STAGE'] + ']' +  '[' + cur_row['FUEL_CAT'] + ']'
          if name not in full_df.columns:
            full_df[name] = ''

          #fill data into cell that have correspond 'TIME_PERIOD'
          num_mask = (full_df['TIME_PERIOD'].dt.year == cur_row['TIME_PERIOD'])

          full_df.loc[num_mask, name] = cur_row['OBS_VALUE']

      except Exception as e:
        msg = 'Error! '+str(e)


    return msg, full_df

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Relevant df functione--------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  def relevant_df(df, full_df):
    #create relevant df
    #relevant_df = df[:156]
    relevant_df = df[~df['Dataset'].str.contains('Fossil Fuel Support ')]
    msg = ''
    for index, row in relevant_df.iterrows():

      #take only data on OECD level
      if row['Area Available'] == 'OECD':
        try:
          data = get_from_oecd(row['API'])

          #go through every row in current dataset
          for idx, cur_row in data.iterrows():

            #remove blank part in name when Measure or Unit/Transformation/Adjustment is empty
            if pd.isnull(row['Measure']) and pd.isnull(row['Unit/Transformation/Adjustment']):
              name = row['Dataset']
            elif pd.isnull(row['Unit/Transformation/Adjustment']) and not pd.isnull(row['Measure']):
              name = row['Dataset'] + '[' + row['Measure'] + ']'
            elif pd.isnull(row['Measure']) and not pd.isnull(row['Unit/Transformation/Adjustment']):
              name = row['Dataset'] + '[' + row['Unit/Transformation/Adjustment'] + ']'
            else:
              name = row['Dataset'] + '[' + row['Measure'] + ']' +  '[' + row['Unit/Transformation/Adjustment'] + ']'

            if name not in full_df.columns:
              full_df[name] = ''

            num_mask = (full_df['TIME_PERIOD'] == cur_row['TIME_PERIOD'])

            full_df.loc[num_mask, name] = cur_row['OBS_VALUE']

        except Exception as e:
          msg = 'Error! '+str(e)

    return msg, full_df

  #----------------------------------------------------------------------------------------------------#
  #-----------------------data country function--------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  def data_country(df, full_df):
    #country_df = df[:156]
    country_df = df[~df['Dataset'].str.contains('Fossil Fuel Support ')]
    msg = ''

    for index, row in country_df.iterrows():

      #take data on countries level (not OECD)
      if row['Area Available'] != 'OECD':
        try:
          data = get_from_oecd(row['API'])

          #go through every row in current dataset
          for idx, cur_row in data.iterrows():

          #remove blank part in name when measure or Unit/Transformation/Adjustment is empty
            if pd.isnull(row['Measure']) and pd.isnull(row['Unit/Transformation/Adjustment']):
              name = row['Dataset'] + '[' + cur_row['REF_AREA'] + ']'
            elif pd.isnull(row['Unit/Transformation/Adjustment']) and not pd.isnull(row['Measure']):
              name = row['Dataset'] + '[' + cur_row['REF_AREA'] + ']' + '[' + row['Measure'] + ']'
            elif pd.isnull(row['Measure']) and not pd.isnull(row['Unit/Transformation/Adjustment']):
              name = row['Dataset'] + '[' + cur_row['REF_AREA'] + ']' + '[' + row['Unit/Transformation/Adjustment'] + ']'
            else:
              name = row['Dataset'] + '[' + cur_row['REF_AREA'] + ']' + '[' + row['Measure'] + ']' +  '[' + row['Unit/Transformation/Adjustment'] + ']'

            if name not in full_df.columns:
              full_df[name] = ''

            num_mask = (full_df['TIME_PERIOD'] == cur_row['TIME_PERIOD'])

            full_df.loc[num_mask, name] = cur_row['OBS_VALUE']


        except Exception as e:
          msg = 'Error! '+str(e)  
    return msg, full_df

  #----------------------------------------------------------------------------------------------------#
  #-----------------------Update and export data-------------------------------------------------------#
  #----------------------------------------------------------------------------------------------------#
  def update():
    #fossil data
    fossil_df(df, full_df)

    #relevant data
    relevant_df(df, full_df)

    #country level data
    data_country(df, full_df)

    file_name = 'full_data.xlsx'
    full_df.to_excel(file_name)
    print('full done')

  update()


automation()