# AI03 — Apne Laptop Par AI Locally Kaise Chalayein?

_Read / explain each slide using these notes._

## Slide 1

दोस्तों, सोचो अगर आपका अपना ChatGPT जैसा AI आपके laptop में ही चले, बिना internet के, बिना किसी subscription के, और आपकी कोई बात किसी company के server पर जाए ही ना। सुनने में जादू लगता है ना? पर ये बिल्कुल possible है, और इसका नाम है — AI locally चलाना। आज Katixo KhojLab की इस episode में हम सीखेंगे कि Ollama नाम के एक free tool से अपने laptop पर AI कैसे चलाएँ, बिल्कुल आसान Hinglish में, step by step. चलिए शुरू करते हैं।

## Slide 2

सबसे पहले समझते हैं — locally AI चलाने का मतलब क्या है? आम तौर पर जब आप ChatGPT use करते हो, तो आपकी बात internet के ज़रिए एक बड़े server पर जाती है, वहाँ जवाब बनता है और वापस आता है। locally चलाने में AI model आपके अपने laptop में download हो जाता है, और सारा काम आपके device पर ही होता है। मतलब internet की ज़रूरत नहीं, पैसे नहीं लगते, और आपकी privacy पूरी तरह आपके पास रहती है। ये उन लोगों के लिए बढ़िया है जो privacy और control चाहते हैं।

## Slide 3

अब बात करते हैं Ollama की, जो ये सब आसान बना देता है। Ollama एक free और open-source tool है, जिसे install करने के बाद आप एक छोटे command से कोई भी AI model download करके चला सकते हो। ये Windows, Mac और Linux तीनों पर चलता है। इसका सबसे बड़ा फायदा ये है कि आपको कोई complicated coding या technical setup करने की ज़रूरत नहीं। बस एक बार install करो, एक command चलाओ, और आपका AI तैयार। इसी की वजह से locally AI चलाना अब आम लोगों के लिए भी आसान हो गया है।

## Slide 4

अब एक ज़रूरी बात — क्या आपका laptop इसके लिए ठीक है? देखो, AI models थोड़े भारी होते हैं, इसलिए laptop में कम से कम आठ GB RAM होनी अच्छी रहती है, सोलह GB तो और बढ़िया है। छोटे models आठ GB पर भी ठीक चल जाते हैं, बस थोड़े धीरे। आपके laptop में कुछ GB जगह भी खाली होनी चाहिए, क्योंकि model download होकर store होता है। अगर आपके पास graphics card यानी GPU है, तो जवाब और तेज़ आएँगे, पर ज़रूरी नहीं, normal laptop पर भी काम चल जाता है।

## Slide 5

अब असली step शुरू — Ollama install कैसे करें। पहला step — अपने browser में जाओ ollama dot com पर, ये इसकी official website है। वहाँ download का button मिलेगा, अपने operating system के हिसाब से, Windows या Mac, version download कर लो। दूसरा step — download हुई file को खोलकर normal software की तरह install कर लो, बस next-next करते जाओ। install होने के बाद Ollama background में चलने लगता है। बस इतना करते ही आपका setup आधा पूरा हो गया, अगला step और भी आसान है।

## Slide 6

अब बारी है model चलाने की, और यहीं असली मज़ा है। अपने laptop पर Command Prompt या Terminal खोलो, ये एक black window जैसी दिखती है। अब उसमें एक छोटी सी line type करो — ollama run llama3 — और Enter दबा दो। पहली बार ये model को internet से download करेगा, जिसमें थोड़ा time लग सकता है, इसलिए धीरज रखो। एक बार download हो गया, तो अगली बार ये बिना internet के तुरंत खुल जाएगा। बस यहीं आपका अपना local AI तैयार हो जाता है।

## Slide 7

Download पूरा होते ही, उसी window में आपको लिखा दिखेगा — Send a message. अब आप यहीं अपने सवाल type कर सकते हो, बिल्कुल ChatGPT की तरह। जैसे लिखो — मुझे एक छोटी कहानी सुनाओ, या किसी topic को आसान भाषा में समझाओ। AI आपके laptop पर ही सोचकर जवाब बना देगा, बिना internet के। बातचीत खत्म करनी हो तो बस slash bye टाइप करो या window बंद कर दो। मुबारक हो, अब आपके पास अपना personal, offline AI assistant है, जो पूरी तरह आपके control में है।

## Slide 8

एक मज़ेदार बात — Ollama पर सिर्फ़ एक model नहीं, कई तरह के models उपलब्ध हैं। जैसे llama3 आम बातचीत के लिए बढ़िया है, वहीं phi और gemma जैसे छोटे models कम RAM वाले laptops पर तेज़ चलते हैं। coding में मदद के लिए भी अलग models होते हैं, जैसे codellama. आप ollama dot com पर इनकी पूरी list देख सकते हो। किसी भी model को चलाना उतना ही आसान है, बस run के बाद उसका नाम बदल दो। यानी एक tool, और ढेर सारे AI options आपकी उँगलियों पर।

## Slide 9

अब कुछ ज़रूरी tips. पहली — अगर आपका laptop थोड़ा slow है या RAM कम है, तो छोटा model चुनो, जैसे phi या gemma, ये हल्के और तेज़ होते हैं। दूसरी — पहली बार model download करते वक्त अच्छा internet रखो, पर उसके बाद आपको internet की ज़रूरत नहीं। तीसरी — एक साथ बहुत भारी model मत चलाओ अगर laptop garam हो रहा हो या hang कर रहा हो, तो छोटे model पर आ जाओ। धीरे-धीरे try करके देखो कि कौन सा model आपके laptop पर सबसे अच्छा चलता है।

## Slide 10

अब एक ईमानदार बात — local AI के फायदे भी हैं और थोड़ी सीमाएँ भी। फायदा ये कि ये free है, offline चलता है, और privacy पूरी आपके पास रहती है। पर सीमा ये कि laptop पर चलने वाले छोटे models, ChatGPT जैसे बड़े online models जितने ताकतवर नहीं होते, जवाब थोड़े simple हो सकते हैं और speed आपके laptop पर निर्भर करती है। तो रोज़मर्रा के कामों, सीखने और privacy वाली बातों के लिए ये बढ़िया है, पर बहुत भारी कामों के लिए expectations सही रखो।

## Slide 11

तो चलिए अब तक की पूरी बात का एक quick recap कर लेते हैं, तीन आसान points में। पहला — locally AI चलाने का मतलब है AI आपके अपने laptop पर, बिना internet और बिना पैसे के, पूरी privacy के साथ। दूसरा — Ollama एक free tool है, बस ollama dot com से install करो, और command में ollama run llama3 लिखकर अपना AI चला लो। तीसरा — अपने laptop के हिसाब से सही model चुनो, छोटे models हल्के होते हैं, और याद रखो local models online ChatGPT जितने भारी नहीं होते।

## Slide 12

तो दोस्तों, आज आपने एक बहुत ही powerful चीज़ सीखी — अपना खुद का AI, अपने laptop पर, पूरी तरह free और private. ये technology पहले सिर्फ़ बड़ी companies के पास थी, और आज आप इसे घर बैठे चला सकते हो। तो आज ही Ollama install करो, अपना पहला model चलाओ, और इस कमाल को खुद महसूस करो। ऐसी और AI tips ke liye Katixo KhojLab subscribe करें, और इस video को अपने दोस्तों के साथ ज़रूर share करें। मिलते हैं अगली episode में!

