def distance(string_1, string_2):
    '''
    Calcuate the Levenshtein distance, which measures how many characters
    have to be changed, inserted or deleted to get from one string to another.
    '''

    if len(string_1) < len(string_2):
        return distance(string_2, string_1)

    previous_row = range(len(string_2) + 1)
    for i, character_1 in enumerate(string_1):
        current_row = [i + 1]
        for j, character_2 in enumerate(string_2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (character_1 != character_2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]
