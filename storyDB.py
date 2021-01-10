# 建立故事內容及關鍵字資料庫
from allennlp.predictors.predictor import Predictor
import copy
from nltk.stem import WordNetLemmatizer
from googletrans import Translator
import createLibrary

story_name = "Fairy friends"
content_list = []
words = ''


def createStory():
    global words
    createLibrary.addBook(story_name, '公主')
    path = "story/" + story_name + ".txt"
    f = open(path, mode='r')
    words = f.read()
    f.close()


def coReference():
    # 紀錄每個角色出現次數
    # tempMax = 0
    # tempProtagonist = ''
    global content_list
    createStory()
    content = words.replace('\n', ' ')
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
        temp = ' '.join(result['document'][result['clusters'][i][0][0]:result['clusters'][i][0][1] + 1])
        # 額外處理
        if story_name == "Fairy friends" and temp == 'Patch , a bad elf':
            temp = 'Patch'
        # print(temp)

        for j in result['clusters'][i]:
            count += 1
            # print(str(j) + ":" + str(result['document'][j[0]:j[1] + 1]), end=',')
            # print(' '.join(result['document'][j[0]:j[1] + 1]))
            # print("story_list", end=':')
            # print(content_list[j[0]])
            if j[0] == j[1]:
                content_list[j[0]] = temp
        # 計算出現次數
    #     if count > tempMax:
    #         tempMax = count
    #         tempProtagonist = temp
    #
    #     print("出現次數：" + str(count), end='\r\n\r\n')
    # print('主角出現'+str(tempMax) + "次：" + tempProtagonist + '\n')


def story_analysis():
    coReference()
    contain_keyword = False

    storyPhraseList = words.split('\n')

    story_2 = ' '.join(content_list)
    story_2 = story_2.replace(' . ', ' . \r\n')
    if story_name == "Fairy friends":
        story_2 = story_2.replace('a mouse ! a mouse', 'a mouse.\r\na mouse').replace('elf ! Patch',
                                                                                      'elf.\r\nPatch').replace(
            'Patch . \r\nGo away', 'Patch . Go away').replace('elf ! " Lily', 'elf ! " \r\nLily').replace('too ! " a',
                                                                                                          'too !\r\n" a')
    if story_name == "Sleeping Beauty":
        story_2 = story_2.replace('die . \r\na', 'die . a').replace('years . \r\n"', 'years . " \r\n')
    print(story_2)
    story_2_PhraseList = story_2.split('\r\n')
    print(story_2_PhraseList)

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
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                entityName.append(result['words'][j])
                continue
            if result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux':
                v = True
                word = wnl.lemmatize(result['words'][j], 'v')
                verbName.append(word.lower())
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
            # story_2_PhraseList[i] = story_2_PhraseList[i].split('"')[1].split('"')[0]
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
                    v_list.append(result['words'][j].lower())
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
            try:
                sentence_Translate = translator.translate(storyPhraseList[i], src="en", dest="zh-TW").text
                # 額外處理翻譯問題
                if story_name == "Fairy friends":
                    missing_patch = ['補丁', '帕奇']
                    missing_fairy = ['仙女', '童話']
                    for word in missing_patch:
                        sentence_Translate = sentence_Translate.replace(word, 'Patch')
                    for word in missing_fairy:
                        sentence_Translate = sentence_Translate.replace(word, '精靈')
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