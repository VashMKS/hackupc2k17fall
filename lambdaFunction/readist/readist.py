import time
import requests
from PIL import Image
from io import BytesIO


def readist_handler(event, context):
    return event.doallstuff(context)


if __name__ == "__main__":
    class Event:
        def __init__(self):
            self._url = 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/RecognizeText'
            self._key = '0f5710b332d54cefa55e2bb9495aef8d'
            self._maxNumRetries = 10

        def processRequest(self, json, data, headers, params):
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
                response = requests.request('post', self._url, json=json, data=data, headers=headers, params=params)

                if response.status_code == 429:
                    print("Message: %s" % (response.json()))
                    if retries <= self._maxNumRetries:
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

        def getOCRTextResult(self, operationLocation, headers):
            """
            Helper function to get text result from operation location

            Parameters:
            operationLocation: operationLocation to get text result, See API Documentation
            headers: Used to pass the key information
            """

            retries = 0
            result = None

            while True:
                response = requests.request('get', operationLocation, json=None, data=None, headers=headers,
                                            params=None)
                if response.status_code == 429:
                    print("Message: %s" % (response.json()))
                    if retries <= self._maxNumRetries:
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

        def writetohtml(self, jsondata, image):

            htmlfile = ''
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
                $(elements[i]).textfill({ maxFontPixels: 100 });
                console.log("insi")
             }
        });
        </script>
        </head>
        <body>

            '''

            preplate = '<div style ="position:absolute;left:0px;top:0px; width:' + str(
                image.size[0]) + 'px;height:' + str(image.size[1]) + 'px;border: 1px solid black;"></div>'
            end = '</body></html>'
            htmlfile += begin + preplate
            for line in range(0, len(jsondata['recognitionResult']['lines'])):
                lines = jsondata['recognitionResult']['lines'][line]
                tl = (lines['boundingBox'][0], lines['boundingBox'][1])
                tr = (lines['boundingBox'][2], lines['boundingBox'][3])
                br = (lines['boundingBox'][4], lines['boundingBox'][5])
                bl = (lines['boundingBox'][6], lines['boundingBox'][7])
                height = bl[1] - tl[1]
                width = br[0] - bl[0]

                template = '<div class = "jtextfill"  style = " position:absolute; left:' + str(
                    tl[0]) + 'px;top:' + str(tl[1]) + 'px;width:' + str(width) + 'px;height:' + str(height) + '">'
                endplate = '</div>'
                htmltext = template + '<span>' + jsondata['recognitionResult']['lines'][line][
                    'text'] + '</span>' + '\n' + endplate

                htmlfile += htmltext
            htmlfile += end
            return htmlfile

        def preprocessing(self, image):
            maxSize = 3200
            if image.size[0] > image.size[1]:
                x = image.size[0]
            else:
                x = image.size[1]

            if x > maxSize:
                ratio = maxSize / x
                newlenght = image.size[0] * ratio
                newheight = ratio * image.size[1]
                v = [int(newlenght), int(newheight)]
                image = image.resize(v)
            return image

        def doallstuff(self, url):

            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            #image = self.preprocessing(img)
            image = img
            print(image.size)
            # Computer Vision parameters
            params = {'handwriting': 'true'}

            headers = dict()
            headers['Ocp-Apim-Subscription-Key'] = self._key
            headers['Content-Type'] = 'application/json'

            json = {'url':url}
            data = None
            result = None
            operationLocation = self.processRequest(json, data, headers, params)


            if (operationLocation != None):
                headers = {}
                headers['Ocp-Apim-Subscription-Key'] = self._key
                while True:
                    time.sleep(1)
                    result = self.getOCRTextResult(operationLocation, headers)
                    if result['status'] == 'Succeeded' or result['status'] == 'Failed':
                        break

            # Load the original image, fetched from the URL
            if result is not None and result['status'] == 'Succeeded':
                return self.writetohtml(result, image)



    context = 'https://cdn.discordapp.com/attachments/368544413560864770/368564818766069760/image.jpg'
    event = Event()
