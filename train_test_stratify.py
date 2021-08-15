import argparse
import logging
import csv
import os
import random
from tqdm import tqdm

########################## A stratify python script ##########################
####### Splitting a csv file into test and train sets, while also stratifying
####### The sets.
####### 1. Select a column to stratify
####### 2. Choose the ratio of the test, and train sets
####### 3. Run the script with the command : python test_train_stratify.py 'your_file.csv' ratio column True/False(shuffle)
####### For example: python test_train_stratify.py data.csv 0.3 device True
#######                                            file name ratio column shuffle
######################## Made by Oriel / Xcompanygames ######################


formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def setup_logger(name, log_file, level=logging.INFO):
    """setup a logger"""
    handler = logging.FileHandler(log_file, 'w', 'utf-8')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


program_logger = setup_logger('train_test_logger', 'train_test_logger.log')


def valid_ratio(num):
    """
    :param num: a number
    :return: check if the number is between 0-1, return False, if not
    """
    if num > 1:
        program_logger.error(f'invalid ratio, input cannot be bigger than 1')
        print('invalid ratio, input is bigger than 1')
        return False
    if num < 0:
        program_logger.error(f'invalid ratio, input cannot be negative')
        print('invalid ratio, input cannot be negative')
        return False
    return True


def is_empty_csv(file_name):
    """
    took that code from here: https://stackoverflow.com/questions/55495075/how-to-check-csv-file-is-empty-in-python
    :param file_name: a file name
    :return: if the csv file is empty
    """
    with open(file_name) as csvfile:
        reader = csv.reader(csvfile)
        for i, _ in enumerate(reader):
            if i:  # found the second row
                return False
    return True


def valid_file_name(file_name):
    """
    :param file_name: a file name
    return false if there is a problem with the file name
    """

    try:
        f = open(file_name, 'rb')
    except FileNotFoundError:
        program_logger.error(f"File {file_name} not found.  Aborting")
        print(f"File {file_name} not found.")
        return False
    except OSError:
        program_logger.error(f"OS error occurred trying to open {file_name}")
        print(f"OS error occurred trying to open {file_name}")
        return False
    if file_name[-4:] != '.csv':
        program_logger.error(f'invalid format, needs to be a csv file')
        print(f'invalid format, needs to be a csv file')
        return False

    if os.stat(file_name).st_size == 0:
        program_logger.error(f'File is empty')
        print(f'File is empty')
        return False

    if is_empty_csv(file_name):
        program_logger.error(f'CSV file got no entries')
        print(f'CSV file got no entries')
        return False

    return True


def valid_stratify(file_name, stratify):
    """
    :param file_name: a file name
    :param stratify: a column to stratify
    return false if the column name isn't in the file
    """
    with open(file_name, newline='', encoding='utf8') as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            list_of_column_names = list(row.keys())
            break
    if stratify in list_of_column_names:
        return True
    program_logger.error(f'stratify column name is invalid, the input column name: {stratify} is not in the file')
    print(f'stratify column name is invalid, the input column name: {stratify} is not in the file')
    return False


def stratify_info_train_test(file_name, stratify_column, ratio):
    """
    :param file_name: get a file name
    :param stratify_column: get a name of a column to stratify
    :param ratio: get ratio number of train or test
    :return:
    1. 2 dictionaries of train and test, each represents a count
    of unique value appearances for every value in the column to be stratified.
    2. A list with the file's column names
    """
    program_logger.info(f'Opening the file')
    with open(file_name, newline='', encoding='utf8') as input_file:
        reader = csv.DictReader(input_file)
        category_dict = {}

        ############################ A little explanation on category_dict ##########################

        # category_dict will contain the appearance count on each value, in the data
        # so if we have device1, device2, and device3
        # category_dict might look like this: {device1:55 device2:22 and device:6}
        # So that means we have 55 entries of device1, 22 entries of device2 and 6 entries of device3

        # After that we splits the category to 2 sets
        #                                  ------> train_dict                #
        #  category_dict ---- (split by ratio)                               #
        #                                  ------> test_dict                 #

        #############################################################################################

        save_column_flag = True
        # A boolean to check if we finish reading the first line
        for row in tqdm(reader):
            if save_column_flag:
                # After reading the first line, we want to save the keys of the dictionary to use them later
                # in the writing function
                list_of_column_names = list(row.keys())
                save_column_flag = False
                # finish the action

            curr_row_cat = row[stratify_column]
            # If the key existing in the dict we will add 1
            # If not we will create it
            if curr_row_cat not in category_dict:
                category_dict[curr_row_cat] = 1
            else:
                category_dict[curr_row_cat] += 1

    # We can't stratify 1 entry of a category
    if 1 in category_dict.values():
        program_logger.info('Cannot stratify category with only 1 entry')
        print('Cannot stratify category with only 1 entry')
        return False

    # We will split category_dict to two sets train and test:
    test_dict = {k: int(ratio * category_dict[k]) for k in category_dict}
    train_dict = {k: int(category_dict[k] - test_dict[k]) for k in category_dict}


    program_logger.info('Finished reading the file, and extracting the relevant info')
    print('\nFinished reading the file, and extracting the relevant info')
    return train_dict, test_dict, list_of_column_names


def delete_empty_set(test_size):
    """
    :param test_size: the test_size ratio
    :return: delete train if the size is 1
             delete test if the size is 0
    """
    if test_size == 1:
        os.remove('train.csv') if os.path.exists('train.csv') else None
    elif test_size == 0:
        os.remove('test.csv') if os.path.exists('test.csv') else None


def train_test_write(file_name, train_dict, test_dict, list_of_column_names, stratify_column, test_size, shuffle):
    """
    :param shuffle: shuffle the split, True or False for shuffling
    :param test_size: The ratio of the test set
    :param file_name: The file name
    :param train_dict: A dictionary contains values and
    number of appearances in the train dataset for each value in the column selected to stratify
    :param test_dict: A dictionary contains values and
    number of appearances in the test dataset for each value in the column selected to stratify
    :param list_of_column_names: a list represents the columns in the file
    :param stratify_column: a selected column to stratify

    The function write 2 files, train.csv and test.csv represents the two sets.
    """
    with open(file_name, newline='') as input_file:
        reader = csv.DictReader(input_file)
        program_logger.info(f'Opening the file again, starting to write the splits into files')
        print('Opening the file again, starting to write the splits into files')

        with open('train.csv', 'w', newline='') as train_file:
            with open('test.csv', 'w', newline='') as test_file:
                # Define the writer
                train_writer = csv.DictWriter(train_file, fieldnames=list_of_column_names)
                test_writer = csv.DictWriter(test_file, fieldnames=list_of_column_names)
                # Write the columns:
                train_writer.writeheader()
                test_writer.writeheader()

                if shuffle:
                    print('shuffling the splits')
                    program_logger.info(f'shuffling the splits')


                    for row in tqdm(reader):
                        rand_num = random.randint(0, 1)
                        curr_row_cat = row[stratify_column]
                        if test_dict[curr_row_cat] == 0:
                            rand_num = 0
                        if train_dict[curr_row_cat] == 0:
                            rand_num = 1
                        if rand_num == 0:
                            train_writer.writerow(row)
                            train_dict[curr_row_cat] -= 1
                        elif rand_num == 1:
                            test_writer.writerow(row)
                            test_dict[curr_row_cat] -= 1
                else:
                    for row in tqdm(reader):
                        curr_row_cat = row[stratify_column]
                        if train_dict[curr_row_cat] != 0:
                            # if category count is not 0, we will write the row
                            train_writer.writerow(row)
                            train_dict[curr_row_cat] -= 1
                        else:
                            test_writer.writerow(row)
                            test_dict[curr_row_cat] -= 1

        program_logger.info(f'Finished, splits created as files')
        print('Finished, splits created as files')

        # We will delete the file if it's empty
        delete_empty_set(test_size)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        program_logger.info(f'Boolean value expected')
        raise argparse.ArgumentTypeError('Boolean value expected.')


def define_parser():
    """
    Setup the arguments from the input parameters
    :return: args dict with file_name, ratio, and stratify column name
    """
    parser = argparse.ArgumentParser(description='file_name, ratio value, stratify column')
    parser.add_argument('file_name', action='store', type=str, help='file name to be splitted.')
    parser.add_argument('test_size', action='store', type=float, help='test_size')
    parser.add_argument('stratify', action='store', type=str, help='stratify column')
    parser.add_argument('shuffle', action='store', type=str, help='shuffle the sets or not')

    args = parser.parse_args()
    return args


def run():
    """
    Create 2 files, train.csv and test.csv
    """
    args = define_parser()
    test_size = args.test_size
    stratify = args.stratify
    file_name = args.file_name
    shuffle = str2bool(args.shuffle)

    if not valid_file_name(file_name):
        return False
    if not valid_ratio(test_size):
        return False
    if not valid_stratify(file_name, stratify):
        return False

        ###################################################### The Process ####################################################

        # Get relevant info from the data, the proportion of unique values in the category we selected to stratify
        # After that we will iterate on the file again, this time we will do the following:

        # We will iterate on each row, when we meet a row, we will check what is the count of the value the row haves
        # in the train or test dicts.

        # For example, we selected the category of device to stratify, in it we have 3 unique values, so it might look
        # like this: {device1:55 device2:22 and device:6}

        # now we met a line that have a value: device2, so we got to the dict above, we remove 1 from count so now it's:
        # {device1:55 device2:21 and device:6}

        # We do that until all values in the train set are 0, so if this dict: {device1:55 device2:22 and device:6}
        # was the train set, we will iterate until it looks like this:
        # {device1:0 device2:0 and device:0}

        # After that we will keep iterating on the test set, until all value counts are 0 there too

        # Each time we go over a row, we will write it into a csv file

        # In the end we will have the same proportions in the train and in the test of a certain column

        # The function stratify_info_train_test will return False, if something is wrong

        ######################################################################################################################

    train_dict, test_dict, list_of_column_names = stratify_info_train_test(file_name, stratify, test_size)

    train_test_write(file_name, train_dict, test_dict, list_of_column_names, stratify, test_size, shuffle)


if __name__ == '__main__':
    run()
