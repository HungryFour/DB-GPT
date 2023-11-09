import requests
import os
import numpy as np
import re
from scipy import spatial  # for calculating vector similarities for search
import pdb
import time
import logging

try:
    import openai
    from openai.error import OpenAIError
except ImportError:
    is_openai_available = False
    logging.warning("openai package is not installed")
else:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    openai.proxy = os.environ.get("http_proxy")
    if openai.proxy is None:
        openai.proxy = os.environ.get("HTTP_PROXY")
    if openai.api_key is None:
        logging.warning(
            "OpenAI API key is not set. Please set the environment variable OPENAI_API_KEY"
        )
        is_openai_available = False
    else:
        is_openai_available = True


similarity = lambda x, y: 1 - spatial.distance.cosine(x, y)


def combine_similar_answers(text, output_format='str'):

    if output_format == 'str':
        text = text.strip()
        tmp_sentences = re.split(r'(?<=[^.])\.(?:\s|\n|$)|\n', text)
    else:
        tmp_sentences = text

    # compute text embedding (1536 dimen) for each sentence
    sentences = []
    for sentence in tmp_sentences:
        
        sentence = sentence.strip()
        
        if sentence != '':
            is_embedded = False
            k = 0
            while not is_embedded and k < 10:
                try:
                    response = openai.Embedding.create(
                        input=sentence,
                        model="text-embedding-ada-002"
                    )
                    
                    if "data" in response:
                        embedding = response['data'][0]['embedding']
                        is_embedded = True
                    else:
                        time.sleep(0.01)
                        k += 1
                except OpenAIError as e:
                    print("OpenAI API error: {}".format(e))
                    time.sleep(0.01)
                    pass

            if is_embedded == True:
                sentences.append({"text": sentence, "embedding": embedding})

    # Compare sentences
    combined_sentences = []
    checked_indices = []

    for i in range(len(sentences)):
        if i in checked_indices:
            continue
        similar_sentences = [sentences[i]["text"]]
        for j in range(i + 1, len(sentences)):
            score = similarity(sentences[i]["embedding"], sentences[j]["embedding"])
            
            if score > 0.8:
                similar_sentences.append(sentences[j]["text"])
                checked_indices.append(j)

        if len(similar_sentences) > 1:
            # for s in similar_sentences:
            #     print(s+'\n'+'====')
            pass

        if similar_sentences[0][-1] != '.':
            similar_sentences[0] = similar_sentences[0] + '.'

        combined_sentences.append(similar_sentences[0])

    if output_format == 'str':
        updated_response = '\n'.join(combined_sentences)
    else:
        updated_response = combined_sentences

    return updated_response

if __name__ == '__main__':
    text = """
[Chief DBA]: The identified root causes of the anomaly are high CPU usage due to the high number of running processes and high load averages, slow queries, and high memory usage due to complex queries, insufficient memory allocation, and the possibility of disk spill.
Optimize the slow queries by analyzing their execution plans, identifying any missing indexes, and tuning the queries accordingly
Polisih the slow queries by checking their execution plans, identifying any missing indexes, and tuning the queries accordingly
Monitor and manage the number of running processes on the node, ensuring that it remains within acceptable limits
Investigate and address any system or infrastructure issues that may be contributing to the high load averages
Consider scaling up or adding more resources to the system if the current CPU usage is consistently high and impacting performance
Add the recommended indexes: ['movie_info#movie_id', 'movie_companies#movie_id', 'keyword#keyword', 'aka_name#person_id'] to reduce cost
Further investigate and optimize the slow queries for better memory utilization
Monitor and adjust the memory allocation parameters like 'work_mem' and 'shared_buffers' to optimize memory usage
Analyze the query plans and consider adjustments to parameters like 'work_mem' and 'shared_buffers' to help reduce or eliminate disk spilling
"""
    print(combine_similar_answers(text))