# S09 — GPS Ko Teri Location Kaise Pata Chalti Hai?

_Read / explain each slide using these notes._

## Slide 1

दोस्तों, ज़रा सोचो — तुम किसी नई जगह पर हो, फ़ोन निकाला, map खोला, और एक नीला dot ठीक तुम्हारे ऊपर! फ़ोन को कैसे पता चला कि तुम पूरी पृथ्वी पर ठीक किस जगह खड़े हो? इसके पीछे है space में घूमते satellites की एक पूरी फ़ौज और गणित का ज़बरदस्त जादू! आज Katixo Shiksha पर हम समझेंगे कि GPS आख़िर काम कैसे करता है — satellites, signals, और एक trick जिसका नाम है trilateration. चलो शुरू करते हैं!

## Slide 2

सबसे पहले — GPS का मतलब है Global Positioning System. यह एक system है करीब 24 से 31 satellites का, जो पृथ्वी से लगभग 20,000 kilometer ऊपर चक्कर लगा रहे हैं. इन्हें इस तरह set किया गया है कि पृथ्वी पर किसी भी जगह से, किसी भी समय, कम से कम 4 satellites आसमान में दिख सकें. यह system असल में अमेरिका ने बनाया था. आज भारत का अपना system भी है — NavIC, यानी Navigation with Indian Constellation. यानी अब हमारे अपने satellites भी रास्ता दिखाते हैं!

## Slide 3

अब असली खेल समझो. हर GPS satellite लगातार एक radio signal भेजता रहता है. इस signal में दो ज़रूरी जानकारियाँ होती हैं — एक, satellite की अपनी सही location, और दो, ठीक वो समय जब signal भेजा गया. तुम्हारे फ़ोन में एक GPS receiver होता है जो इन signals को पकड़ता है. यहाँ key idea यह है — फ़ोन सिर्फ signals सुनता है, खुद space में कुछ नहीं भेजता. यानी GPS पूरी तरह one-way है, इसीलिए दुनिया में जितने चाहो उतने devices एक साथ बिना भीड़ के इसका इस्तेमाल कर सकते हैं!

## Slide 4

अब सबसे smart हिस्सा — distance नापना. signal radio waves के रूप में आता है, जो light की speed से चलता है, यानी करीब 3 lakh kilometer प्रति second. तुम्हारा फ़ोन देखता है कि signal भेजा कब गया था, और पहुँचा कब. इन दोनों समय का फ़र्क बताता है signal ने कितना time लिया. फिर simple formula — distance बराबर speed गुणा time. time को light की speed से गुणा करो, और मिल गई satellite से तुम्हारी exact दूरी! यानी GPS असल में एक बेहद सटीक stopwatch की तरह काम करता है.

## Slide 5

पर एक satellite से दूरी पता होना काफ़ी नहीं. मान लो एक satellite कहता है, तुम मुझसे 20,000 km दूर हो. इसका मतलब तुम उस satellite के चारों ओर एक विशाल गोले की सतह पर कहीं भी हो सकते हो — पर कहाँ, यह पता नहीं. एक दूरी सिर्फ एक circle या sphere देती है, एक पक्का point नहीं. तो location pinpoint करने के लिए हमें और satellites चाहिए. यहीं से शुरू होती है GPS की असली genius trick, जिसका नाम है trilateration. आगे समझते हैं!

## Slide 6

Trilateration को आसान example से समझो दोस्तों. मान लो किसी ने कहा तुम Delhi से 100 km दूर हो — तुम Delhi के चारों ओर एक circle पर कहीं भी हो. अब कोई और कहे तुम Jaipur से भी 200 km दूर हो — अब दोनों circles दो जगह काटेंगे. अब तीसरा clue — Agra से 150 km — और ये तीनों circles एक ही point पर मिलेंगे, वही तुम्हारी location! GPS भी बिल्कुल यही करता है, बस circles की जगह satellites से बने spheres का इस्तेमाल करता है आसमान में.

## Slide 7

अब सवाल — कितने satellites चाहिए? तीन satellites से तुम्हारी पृथ्वी पर 2D location — latitude और longitude — निकल सकती है. पर असल दुनिया 3D है, और एक चौथा बड़ा factor है — समय का सही मिलान. तुम्हारे फ़ोन की घड़ी satellites की atomic clocks जितनी perfect नहीं होती. इसलिए GPS चौथे satellite का इस्तेमाल करता है — clock की छोटी सी गलती को सुधारने और तुम्हारी ऊँचाई यानी altitude भी निकालने के लिए. इसीलिए कहा जाता है, GPS को सही काम के लिए कम से कम 4 satellites चाहिए!

## Slide 8

अब एक mind-blowing बात — GPS में Einstein की theory भी काम आती है! satellites की atomic clocks और तुम्हारी ज़मीनी घड़ी के बीच बहुत छोटा सा time फ़र्क आता है. एक तरफ satellites तेज़ चलते हैं, तो special relativity के हिसाब से उनकी घड़ी थोड़ी धीमी होनी चाहिए. दूसरी तरफ वो ऊँचाई पर हैं जहाँ gravity कमज़ोर है, तो general relativity के हिसाब से उनकी घड़ी थोड़ी तेज़ चलती है. कुल मिलाकर हर दिन कुछ microseconds का फ़र्क बनता है. अगर इसे सुधारा न जाए, तो GPS रोज़ कई kilometer गलत हो जाए!

## Slide 9

अब असल ज़िंदगी की एक मुश्किल — GPS हमेशा perfect क्यों नहीं होता? कुछ कारण हैं. एक — ऊँची इमारतों के बीच signal दीवारों से टकराकर bounce होता है, इसे कहते हैं multipath error, इसीलिए शहरों में location कभी-कभी भटकती है. दो — पृथ्वी का वायुमंडल, खासकर ionosphere, signal को थोड़ा धीमा कर देता है. तीन — सुरंग, घनी इमारत या मोटी दीवार के अंदर signal पहुँच ही नहीं पाता. इसीलिए indoors में अक्सर GPS कमज़ोर हो जाता है या नीला dot इधर-उधर कूदता है!

## Slide 10

तो तुम्हारा फ़ोन इन गलतियों से निपटता कैसे है? smart trick — फ़ोन सिर्फ GPS पर निर्भर नहीं रहता. वो Wi-Fi networks और आसपास के mobile towers का भी इस्तेमाल करता है location बेहतर करने के लिए, खासकर indoors. साथ ही फ़ोन के अंदर sensors होते हैं — accelerometer और gyroscope — जो तुम्हारी movement भाँपते हैं. इन सबको मिलाकर फ़ोन एक ज़्यादा सटीक और तेज़ location देता है. इसी combination को कहते हैं assisted GPS — यानी GPS को थोड़ी extra मदद!

## Slide 11

अब सोचो GPS रोज़मर्रा में कहाँ-कहाँ है दोस्तों. सिर्फ Google Maps नहीं! food और cab delivery, खोया हुआ फ़ोन ढूँढना, खेती में सटीक tractors, समुद्र में जहाज़ और आसमान में plane का रास्ता, आपदा में बचाव दल, और बैंक tak — सब GPS की precise timing पर निर्भर करते हैं. यानी आसमान में चुपचाप घूमते कुछ satellites पूरी आधुनिक दुनिया को रास्ता और समय दोनों दे रहे हैं. एक system जिसे हम रोज़ इस्तेमाल करते हैं, पर शायद ही कभी उसका शुक्रिया कहते हैं!

## Slide 12

Quick brain check! तीन सवाल, ज़रा दिमाग लगाओ. पहला — तुम्हारा फ़ोन किसी satellite से अपनी दूरी कैसे नापता है, कौन सा formula इस्तेमाल होता है? दूसरा — कई satellites से दूरियाँ लेकर exact location निकालने वाली trick का नाम क्या है, और सही काम के लिए कम से कम कितने satellites चाहिए? तीसरा — किस महान scientist की relativity theory को GPS में सुधार के लिए इस्तेमाल किया जाता है? अभी video PAUSE करो, सोचो, खुद जवाब दो. फिर answers मिलेंगे!

## Slide 13

जवाब देखते हैं! पहला — फ़ोन देखता है signal भेजने और पहुँचने के बीच का time, फिर formula distance बराबर speed गुणा time लगाता है, जहाँ speed light की speed होती है. दूसरा — उस trick का नाम है trilateration, और सही 3D location के लिए कम से कम 4 satellites चाहिए — चौथा clock की गलती और altitude के लिए. तीसरा — Albert Einstein की relativity theory, special और general दोनों, GPS में time correction के लिए इस्तेमाल होती हैं. तीनों सही? वाह, तुम अब GPS के असली expert हो!

## Slide 14

तो final recap दोस्तों. GPS करीब 30 satellites का system है जो लगातार अपनी location और समय वाले signals भेजते हैं. तुम्हारा फ़ोन signal का travel time नापकर हर satellite से दूरी निकालता है, फिर trilateration से कम से कम 4 satellites की मदद से तुम्हारी exact location pinpoint करता है — और Einstein की relativity time को सटीक रखती है. अगला episode बड़ा मज़ेदार है — Why Is the Ocean Salty, यानी समुद्र का पानी खारा क्यों होता है! Subscribe करना मत भूलना! Bye!

