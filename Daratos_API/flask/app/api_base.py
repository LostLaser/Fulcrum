import sys
from app import app
from flask import request, jsonify, Flask

from app import db_handler
from app import api_exception
from app import bias_prediction

prediction_instance = bias_prediction.Predictor()

@app.route('/')
def info():
    return 'Welcome to the political bias API! Go to /bias if you are wanting to get a prediction!'

@app.route('/health', methods=['GET'])
def home():
    return 'We are up!'

@app.route('/bias', methods=['POST'])
def bias_calc():
    '''
    Endpoint to determine the bias of the specified news article

    Parameters: 
        content (str): String containing English sentences
        verbose (bool): truth value make call return more detailed information

    Returns:
        Json object of the bias details
    '''
    if not request.json:
        raise api_exception.InvalidUsage('Missing json request body', status_code = 400)
    
    json_data = request.get_json()
    content = str(json_data.get('content'))
    verbose = str(json_data.get('verbose'))
    
    if not content or len(content) == 0:
        raise api_exception.InvalidUsage('No content specified', status_code = 204)
    
    try:
        predictions, sentences = prediction_instance.predict_article(content)
    except EnvironmentError:
        raise api_exception.InvalidUsage('Missing prediction resources', status_code = 503)
    
    total_bias = prediction_instance.consolidate_biases(predictions)
    
    if verbose and verbose.lower() == 'true':
        prediction_info = []
        for i in range( min(len(sentences), len(predictions)) ):
            prediction_info.append({ 'sentence': sentences[i],
                                     'prediction': predictions[i] })

        ret_val = {'total_bias': total_bias,
                   'prediction_info': prediction_info}
    else:
        ret_val = {'total_bias': total_bias}
    
    return jsonify(ret_val)

@app.route('/article/xpath', methods=['POST'])
def retrieve_xpath():
    '''
    Endpoint to determine the web scraping details of a news website

    Parameters: 
        domain (str): domain name of a supported news website

    Returns:
        Json object containing the xpath
    '''
    json_data = request.get_json()
    x_path = ""

    if json_data:
        domain = str(json_data.get('domain'))
        x_path = db_handler.get_xpath(domain)

    ret_val = {'domain_xpath': x_path}
    return jsonify(ret_val)

@app.route('/tokenize', methods=['GET'])
def tokenize_sentences():
    '''
    Endpoint to tokenize a string the way Daratos does

    Parameters: 
        content (str): String containing English sentences
  
    Returns: 
        Json object containing the tokenized sentences
    '''
    content = request.form.get('content', type = str)
    
    sentence_fragments = prediction_instance.tokenize_sentences(content)
    output_tokens = []

    for sentence in sentence_fragments:
        output_tokens.append(sentence[0].tolist())

    ret_val = {'tokenized_sentences': output_tokens}

    return jsonify(ret_val)

@app.errorhandler(api_exception.InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response