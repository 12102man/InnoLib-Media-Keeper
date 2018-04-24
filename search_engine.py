import database


def search(parameter, criteria):
    medias = []
    if parameter == 'name':
        if "OR" in criteria:
            criteria = criteria.split("OR")
            media_list = list(database.Media.select())
            for media in media_list:
                flag = False
                for cr in criteria:
                    if cr.strip().lower() in media.name.lower():
                        flag = True
                        break
                if flag:
                    medias.append(media)
        elif "AND" in criteria:
            criteria = criteria.split("AND")
            media_list = list(database.Media.select())
            for media in media_list:
                flag = False
                for cr in criteria:
                    if not cr.strip().lower() in media.name.lower():
                        flag = True
                        break
                if not flag:
                    medias.append(media)

        else:
            medias = list(database.Media.select(lambda c: criteria in c.name))
    elif parameter == 'authors':
        medias = list(database.Media.select(lambda c: criteria in c.authors))
    elif parameter == 'publisher':
        medias = list(database.Media.select(lambda c: criteria in c.publisher))
    elif parameter == 'type':
        medias = list(database.Media.select(lambda c: c.type == criteria))
    elif parameter == 'keywords':
        criteria = criteria.split(", ")
        for cr in criteria:
            medias = medias + list(database.Media.select(lambda c: cr in c.keywords))

    return medias
