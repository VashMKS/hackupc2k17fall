import time
import requests
import cv2
import numpy as np
from PIL import Image
from io import BytesIO


# Import library to display results
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Variables

_url = 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/RecognizeText'
#_key = insert here your key
_maxNumRetries = 10

def processRequest(json, data, headers, params):
    """
    Helper function to process the request to Project Oxford

    Parameters:
    json: Used when processing images from its URL. See API Documentation
    data: Used when processing image read from disk. See API Documentation
    headers: Used to pass the key information and the data type request
    """

    retries = 0
    result = None

    while True:
        response = requests.request('post', _url, json=json, data=data, headers=headers, params=params)

        if response.status_code == 429:
            print("Message: %s" % (response.json()))
            if retries <= _maxNumRetries:
                time.sleep(1)
                retries += 1
                continue
            else:
                print('Error: failed after retrying!')
                break
        elif response.status_code == 202:
            result = response.headers['Operation-Location']
        else:
            print("Error code: %d" % (response.status_code))
            print("Message: %s" % (response.json()))
        break

    return result


def getOCRTextResult( operationLocation, headers ):
    """
    Helper function to get text result from operation location

    Parameters:
    operationLocation: operationLocation to get text result, See API Documentation
    headers: Used to pass the key information
    """

    retries = 0
    result = None

    while True:
        response = requests.request('get', operationLocation, json=None, data=None, headers=headers, params=None)
        if response.status_code == 429:
            print("Message: %s" % (response.json()))
            if retries <= _maxNumRetries:
                time.sleep(1)
                retries += 1
                continue
            else:
                print('Error: failed after retrying!')
                break
        elif response.status_code == 200:
            result = response.json()
        else:
            print("Error code: %d" % (response.status_code))
            print("Message: %s" % (response.json()))
        break

    return result


def showResultOnImage(result, img):
    """Display the obtained results onto the input image"""
    img = img[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(img, aspect='equal')

    lines = result['recognitionResult']['lines']

    for i in range(len(lines)):
        words = lines[i]['words']
        for j in range(len(words)):
            tl = (words[j]['boundingBox'][0], words[j]['boundingBox'][1])
            tr = (words[j]['boundingBox'][2], words[j]['boundingBox'][3])
            br = (words[j]['boundingBox'][4], words[j]['boundingBox'][5])
            bl = (words[j]['boundingBox'][6], words[j]['boundingBox'][7])
            text = words[j]['text']
            x = [tl[0], tr[0], tr[0], br[0], br[0], bl[0], bl[0], tl[0]]
            y = [tl[1], tr[1], tr[1], br[1], br[1], bl[1], bl[1], tl[1]]
            line = Line2D(x, y, linewidth=3.5, color='red')
            ax.add_line(line)
            t = 7
            height = bl[1]-tl[1]
            if height < 15:
                t = 6
            if height > 20:
                t = 8
            if height > 25:
                t = 9
            if height > 30:
                t = 10
            if height > 35:
                t = 15
            if height > 60:
                t = 18

            ax.text((bl[0]+br[0])/2, (bl[1]+tl[1])/2, '{:s}'.format(text),
                    bbox=dict(facecolor='blue', alpha=0.5),
                    fontsize=t, color='white', ha='center', va='center')

    plt.axis('off')
    plt.tight_layout()
    plt.draw()
    plt.show()


def writetohtml(jsondata,image,path):
    path = path[0:-4] + '.html'
    htmlfile = open(path, 'w')
    begin = '''
<html>
<head>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
<script>
    ;(function($) {
    $.fn.textfill = function(options) {
        var fontSize = options.maxFontPixels;
        var ourText = $('span:visible:first', this);
        var maxHeight = $(this).height();
        var maxWidth = $(this).width();
        var textHeight;
        var textWidth;
        do {
            ourText.css('font-size', fontSize);
            textHeight = ourText.height();
            textWidth = ourText.width();
            fontSize = fontSize - 1;
        } while ((textHeight > maxHeight || textWidth > maxWidth) && fontSize > 3);
        return this;
    }
})(jQuery);


$(document).ready(function() {
var elements = document.getElementsByClassName('jtextfill');
    for(var i = 0; i < elements.length; i++ ){
        $(elements[i]).textfill({ maxFontPixels: 36 });
        console.log("insi")
     }
});
</script>
</head>
<body>
    
    '''

    preplate = '<div style ="position:absolute;left:0px;top:0px; width:' + str(image.size[0]) + 'px;height:' + str(image.size[1]) + 'px;border: 1px solid black;"></div>'
    end = '</body></html>'
    htmlfile.write(begin + preplate)
    for line in range(0, len(jsondata['recognitionResult']['lines'])):

        lines = jsondata['recognitionResult']['lines'][line]
        tl = (lines['boundingBox'][0], lines['boundingBox'][1])
        tr = (lines['boundingBox'][2], lines['boundingBox'][3])
        br = (lines['boundingBox'][4], lines['boundingBox'][5])
        bl = (lines['boundingBox'][6], lines['boundingBox'][7])
        height = bl[1] - tl[1]
        width = br[0] - bl[0]

        template = '<div class = "jtextfill"  style = " position:absolute; left:' + str(tl[0]) + 'px;top:' + str(tl[1]) + 'px;width:'+str(width)+'px;height:'+str(height)+'">'
        endplate = '</div>'
        htmltext = template + '<span>' + jsondata['recognitionResult']['lines'][line]['text'] + '</span>' + '\n' + endplate

        htmlfile.write(htmltext)
    htmlfile.write(end)

def preprocessing(path):
    maxSize = 1000
    image = Image.open(path)
    if image.size[0] > image.size[1]:
        x = image.size[0]
    else:
        x = image.size[1]

    if x > maxSize:
        ratio = maxSize/x
        newlenght = image.size[0]*ratio
        newheight = ratio * image.size[1]
        v = [int(newlenght),int(newheight)]
        image = image.resize(v)
    image.save(path, "JPEG", quality=80, optimize=True, progressive=True)



# Load raw image file into memory

def doallstuff(path, url):
    if url != '':
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        path = path + 'url'
        img.save(path, "JPEG", quality=80, optimize=True, progressive=True)

    preprocessing(path)

    with open(path, 'rb') as f:
        data = f.read()
    image = Image.open(path)
    # Computer Vision parameters
    params = {'handwriting': 'true'}

    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = _key
    headers['Content-Type'] = 'application/octet-stream'

    json = None

    operationLocation = processRequest(json, data, headers, params)

    result = None
    if (operationLocation != None):
        headers = {}
        headers['Ocp-Apim-Subscription-Key'] = _key
        while True:
            time.sleep(1)
            result = getOCRTextResult(operationLocation, headers)
            if result['status'] == 'Succeeded' or result['status'] == 'Failed':
                break

    # Load the original image, fetched from the URL
    if result is not None and result['status'] == 'Succeeded':
        data8uint = np.fromstring(data, np.uint8)  # Convert string to an unsigned int array
        img = cv2.cvtColor(cv2.imdecode(data8uint, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        writetohtml(result,image,path)
        showResultOnImage(result, img)

localpath = './data/sample4.jpg'
link = 'https://cdn.discordapp.com/attachments/368544413560864770/368564818766069760/image.jpg'
doallstuff(localpath, '')
