from allennlp.predictors.predictor import Predictor
import copy
# from google.cloud import translate_v2
from nltk.stem import WordNetLemmatizer
from googletrans import Translator
import os
import createLibrary
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'dict/key.json'

story_name = "Fairy friends"
story = 'Lily and Rose liked to help their friends.\r\n Lily saw a bird.\r\n "We can help that bird," she said.\r\n Lily and Rose helped the bird.\r\n Rose saw a cat.\r\n "Now we can help that cat," she said.\r\n Lily and Rose helped the cat.\r\n Lily saw a mouse.\r\n "Now we can help that mouse," she said.\r\n It was not a mouse!\r\n It was Patch, a bad elf.\r\n Patch liked to play tricks.\r\n He had turned into a mouse to trick Lily and Rose.\r\n Rose saw a dog.\r\n "We can help that dog," she said.\r\n Lily and Rose went to help the dog.\r\n It was not a dog.\r\n It was Patch the elf!\r\n He had turned into a dog to trick Lily and Rose.\r\n "Go away, Patch!" said Lily and Rose.\r\n "You are a bad elf!"\r\n Lily saw a fairy.\r\n "We can help that fairy," she said.\r\n "That is not a fairy," said Rose.\r\n "It is Patch. Go away, Patch, you bad elf!"\r\n They saw the fairy, and they saw Patch, too!\r\n "It IS a fairy," said Rose.\r\n "We can help you," said Lily.\r\n Lily and Rose helped the fairy.\r\n Patch turned into a bird and he helped, too.\r\n The fairy was Lily and Rose\'s new friend.\r\n Now Patch was their friend, too.\r\n '
content_list = []


def coReference():
    global content_list
    # 紀錄每個角色出現次數
    characterCount = []
    tempMax = 0
    tempProtagonist = ''

    # Co-reference
    content = story.replace('\r\n', '')
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2020.02.27.tar.gz")
    result_1 = predictor.predict(
        document=content
    )
    result = copy.deepcopy(result_1)

    content_list = result['document']

    # 找出代名詞對應主詞 修改原文
    for i in range(len(result['clusters'])):
        count = 0
        characterCount.append([])
        temp = ' '.join(result['document'][result['clusters'][i][0][0]:result['clusters'][i][0][1] + 1])

        # 額外處理
        if story_name == "Fairy friends" and temp == 'Patch , a bad elf':
            temp = 'Patch'

        # print(temp)

        for j in result['clusters'][i]:
            count += 1
            # print(str(j) + ":" + str(result['document'][j[0]:j[1] + 1]), end=',')
            # print(' '.join(result['document'][j[0]:j[1] + 1]))
            #
            # print("story_list", end=':')
            # print(content_list[j[0]])

            if j[0] == j[1]:
                content_list[j[0]] = temp

        if count > tempMax:
            tempMax = count
            tempProtagonist = temp

    #     print("出現次數：" + str(count), end='\r\n\r\n')
    #
    # print('主角出現'+str(tempMax) + "次：" + tempProtagonist + '\n')


def story_analysis():
    coReference()
    contain_keyword = False

    storyPhraseList = story.split('\r\n ')
    storyPhraseList.remove('')

    story_2 = ' '.join(content_list)
    story_2 = story_2.replace(' . ', ' . \r\n')
    if story_name == "Fairy friends":
        story_2 = story_2.replace('a mouse ! a mouse', 'a mouse.\r\na mouse').replace('elf ! Patch',
                                                                                      'elf.\r\nPatch').replace(
            'Patch . \r\nGo away', 'Patch . Go away').replace('elf ! " Lily', 'elf ! " \r\nLily').replace('too ! " a',
                                                                                                          'too !\r\n" a')
    story_2_PhraseList = story_2.split('\r\n')

    # Dependency Parsing
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")

    counter_speech = False
    entityName = []
    verbName = []

    wnl = WordNetLemmatizer()
    # 找出所有keyword
    for i in range(len(story_2_PhraseList)):
        v = False
        if story_2_PhraseList[i].endswith(', '):
            sentence = story_2_PhraseList[i].replace(',', '')
        else:
            sentence = story_2_PhraseList[i].replace(' .', '')
        result = predictor.predict(
            sentence=sentence
        )
        # print(sentence)
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                entityName.append(result['words'][j])
                continue
            if result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux':
                v = True
                verbName.append(wnl.lemmatize(result['words'][j], 'v'))
                continue
            if v == True and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                entityName.append(result['words'][j])
                continue

    entityInfo = {}
    sort_entity = {}
    for i in entityName:
        entityInfo[i] = {"Frequence": entityName.count(i)}
        sort_entity[i] = entityName.count(i)
    verbInfo = {}
    for i in verbName:
        verbInfo[i] = {"Frequence": verbName.count(i)}
    createLibrary.addBookKeyword(story_name, entityInfo, verbInfo)

    # 排序entity
    main_entity = []
    sort_entity = sorted(sort_entity.items(), key=lambda x: x[1], reverse=True)
    temp = int(len(sort_entity)*0.3)
    for i in sort_entity[:temp]:
        main_entity.append(i[0])
    print("主要entity"+str(main_entity))

    # 抓出主要SVO
    for i in range(len(story_2_PhraseList)):
        speaker = ''
        speak_to = ''
        if '"' in story_2_PhraseList[i]:
            counter_speech_ind = i
            temp = story_2_PhraseList[i].split(' ')
            # 找出speaker
            if story_2_PhraseList[i].replace(' .', '').endswith('said '):
                if temp[(len(story_2_PhraseList[i].split(' ')) - 5)] == 'and':
                    speaker = temp[(len(story_2_PhraseList[i].split(' ')) - 6)] + ' and ' + temp[(len(story_2_PhraseList[i].split(' ')) - 4)]
                else:
                    speaker = temp[(len(story_2_PhraseList[i].split(' ')) - 4)]
            elif story_2_PhraseList[i].replace(' .', '').endswith('" '):
                speaker = ''
            else:
                if temp[(len(story_2_PhraseList[i].split(' ')) - 4)] == 'and':
                    speaker = temp[(len(story_2_PhraseList[i].split(' ')) - 5)] + ' and ' + temp[(len(story_2_PhraseList[i].split(' ')) - 3)]
                else:
                    speaker = temp[(len(story_2_PhraseList[i].split(' ')) - 3)]

            # speak_to
            if counter_speech and (i - counter_speech_ind) == 1:
                speak_to = counter_speech_ind - 1
            elif counter_speech and (i - counter_speech_ind) != 1:
                if speaker in story_2_PhraseList[i]:
                    speak_to = counter_speech_ind - 1

            counter_speech = True
            story_2_PhraseList[i] = story_2_PhraseList[i].split('"')[1].split('"')[0]
        else:
            counter_speech = False

        c1_list = []
        c2_list = []
        v_list = []
        v = False
        if story_2_PhraseList[i].endswith(', '):
            sentence = story_2_PhraseList[i].replace(',', '')
        else:
            sentence = story_2_PhraseList[i].replace(' .', '')
        result = predictor.predict(
            sentence=sentence
        )
        print(sentence)
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c1_list:
                    c1_list.append(result['words'][j])
                    if result['words'][j] in main_entity:
                        contain_keyword = True
                continue
            if result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux':
                v = True
                if result['words'][j] not in v_list:
                    v_list.append(result['words'][j])
                continue
            if v == True and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c2_list:
                    c2_list.append(result['words'][j])
                    if result['words'][j] in main_entity:
                        contain_keyword = True
                continue
        print('S:' + str(c1_list) + ' V:' + str(v_list) + ' O:' + str(c2_list))
        translator = Translator()
        while True:
            # translate_client = translate_v2.Client()
            # source = 'en'
            # target = 'zh-TW'
            try:
                sentence_Translate = translator.translate(storyPhraseList[i], src="en", dest="zh-TW").text
                # sentence_Translate = translate_client.translate(
                #     storyPhraseList[i],
                #     source_language=source,
                #     target_language=target)
                break
            except Exception as e:
                print(e)

        if len(c1_list) == 0:
            c1_list = ''
        if len(c2_list) == 0:
            c2_list = ''
        if len(v_list) == 0:
            v_list = ''
        createLibrary.addBookInfo(story_name, c1_list, v_list, c2_list, story_2_PhraseList[i], sentence_Translate, i, speaker, speak_to, contain_keyword)
        contain_keyword = False
        print()


if __name__ == "__main__":
    # coReference()
    story_analysis()
