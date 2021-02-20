###############################################################################
#
#                                 NOTICE:
#  THIS PROGRAM CONSISTS OF TRADE SECRECTS THAT ARE THE PROPERTY OF
#  Advanced Products Ltd. THE CONTENTS MAY NOT BE USED OR DISCLOSED
#  WITHOUT THE EXPRESS WRITTEN PERMISSION OF THE OWNER.
#
#               COPYRIGHT Advanced Products Ltd 2016-2019
#
###############################################################################

import datetime
import json

from qp_api_server import QPAPIServer
from qp_model import QPModel
from qp_model_run import QPModelRun

# set up model
if __name__ == "__main__": 
    ### QP CODE ###
    # set up model
    server = QPAPIServer('127.0.0.1', 8080)
    model_category = 'demo'
    model_name = 'vol_surface'
    model = QPModel(server, model_category, model_name)   
    model.load()

    date_time = datetime.now().strftime("%Y/%m/%d:%S")
    ### QP CODE ###
    # start with doing analytic prices
    run_name = 'get vol surface ' + date_time
    print('running ' + run_name)
    # reading the last message that was sent
    with model.new_run(run_name, offset_forwards=False, offset=214) as run:        
        # metrics are number got vs not got
        number_of_ivs_got = 0
        number_of_ivs_not_got = 0
        # and time taken

        # get the io
        input = run.get_input()
        output = run.get_output()

        # start timing
        start = timestamp()

        # loop through the list of moneynesses and expiries
        should_read = True
        while(True == should_read):
            input_message = input.read(timeout_milliseconds=3000)
            if(input_message is not None):
                # gets the name, the expiry and price
                instrument_name, expiry, strike = read_data(input_message)
                # get the last trade for that
                iv_base_price = get_iv_base_price(instrument_name)
                # if we got something
                if(iv_base_price is not None):
                    # write the result out
                    output_data = calculate_and_get_out_data(instrument_name, expiry, strike, moneyness, iv )
                    output.write(output_data)
                    # bump that we got an iv
                    number_of_ivs_got = number_of_ivs_got + 1
                else:
                    number_of_ivs_not_got  = number_of_ivs_not_got + 1


        # stop timer
        end = timestamp()
        time_taken = end-start

        
        # set metrics
        run.set_metric_value('demo/time_taken', time_taken)
        run.set_metric_value('demo/number_of_ivs_got', number_of_ivs_got)
        run.set_metric_value('demo/number_of_ivs_not_got', number_of_ivs_not_got)

def get_iv_base_price(instrument_name):
    url = 'https://test.deribit.com/api/v2/public/get_last_trades_by_instrument?count=1&instrument_name=' + instrument_name
    # get response
    response = requests.get(url)

    # if it worked
    if response.status_code in successful_response_code:
        # get response as json object
        return json.loads(response.content.decode('utf-8'))
    else:
        # throw exception
        return None


def calculate_and_get_out_data(instrument_name, expiry, strike, moneyness, iv ):
    # get base price, calculate moneyness
    base_price = float(iv_base_price['index_price'])
    moneyness = (base_price - strike)/strike * 100
    # got iv and turn into a fraction
    iv = float(iv_base_price['iv'])/100

    # turn it into json
    output_data = json.loads('{}')
    output_data['instrument_name'] = instrument_name
    output_data['expiry'] = expiry
    output_data['strike'] = strike
    output_data['moneyness'] = moneyness
    output_data['iv'] = iv
    return output_data


def read_data(input_data):
    input = json.loads(input_data.text)
    instrument_name = input['symbol']
    expiry = int(input['expiry'])
    strike = strike(input['strike'])

    return instrument_name, expiry, strike

def convert_to_datetime(time_in_milliseconds):
    base_datetime = datetime.datetime( 1970, 1, 1 )
    delta = datetime.timedelta( 0, 0, 0, time_in_milliseconds )
    target_date = base_datetime + delta
