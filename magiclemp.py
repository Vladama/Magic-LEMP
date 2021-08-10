import json
import argparse


class MeasuresList():
    """Class representing a list of measures from a music sheet it process
    the intermediate and final list of measure automatically

    Args:
        measure_list (list): list of different measure

        total_number_of_measures (integer): maximum measure on the partition
    """

    def __init__(self, measure_list, total_number_of_measures):
        self.measure_list = measure_list
        self.total_number_of_measures = total_number_of_measures

        self.process()

    def process(self):
        """Function that doing the whole process to transformation a measure 
        list on intermediate and final list of measure

        Args:
            measure_list (list): list of different measure
        """

        self.brs, self.brc, self.segno, self.dacapo, self.coda = self.create_duo()
        self.measure_mid = self.create_mid_sequence(
            self.brs, self.brc, self.segno, self.dacapo, self.coda)
        self.measure_final = self.create_final_sequence(self.measure_mid)

    def create_duo(self):
        """Function that preprocess and create measurement pairs and 

        Args:
            measure_list (list): list of different measure

        Returns:
            list: list of BRS pairs
            list: list of ending pairs
            list: list of segno pairs
            list: list of dacapo pairs
            list: list of coda pairs
        """

        measure_list = self.measure_list
        # Creation of measurement pairs
        brs = self.create_symbole(
            measure_list['repeat_backward'], measure_list['repeat_forward'])
        ending = self.create_symbole(
            measure_list['ending_one'], measure_list['ending_two'])
        segno = self.create_symbole(
            measure_list['dalsegno'], measure_list['segno'])
        coda = self.create_symbole(
            measure_list['tocoda'], measure_list['coda'])
        dacapo = self.create_dacapo(measure_list['dacapo'])

        brs = self.preprocess_out_of_range(brs)
        ending = self.preprocess_out_of_range(ending)
        segno = self.preprocess_out_of_range(segno)
        coda = self.preprocess_out_of_range(coda)
        dacapo = self.preprocess_out_of_range(dacapo)

        # Preprocessing depending on the validation conditions
        brs, ending = self.preprocess_br(brs, ending)
        segno, coda = self.preprocess_coda(dacapo, segno, coda)

        if ending != []:
            brc, brs = self.create_brc(brs, ending)
        else:
            brc = []

        return brs, brc, segno, dacapo, coda

    def create_mid_sequence(self, brs, brc, segno, dacapo, coda):
        """Function that create the intermediate sequence from different jump pair

        Args:
            brs (list): list of BRC pairs
            brc (list): list of BRC 
            segno (list): list of segno pairs
            dacapo (list): list of dacapo pairs
            coda (list): list of coda pairs

        Returns:
            list: list of different jump in the measure sequences
        """

        def sorting_lambda(start): return start[0]
        measure_mid = []

        # Sorting of BRS and BRC
        brs.extend(brc)
        brs.sort(key=sorting_lambda)
        measure_mid.extend(brs)

        # Sorting of Dacapo and Segno
        segno.extend(dacapo)
        segno.sort(key=sorting_lambda)

        if coda != []:
            # If coda exist, adding the first segno or dacapo jump
            measure_mid.append(segno[0])
            del segno[0]

            # Check the coda's placement in the list of dacapo and segno
            for coda_pairs in coda:
                for i, segno_dacapo_pairs in enumerate(segno):

                    if coda_pairs[0] < segno_dacapo_pairs[0] and coda_pairs[1] < segno_dacapo_pairs[0]:
                        segno.insert(i, coda_pairs)
                        break
                else:
                    segno.append(coda_pairs)

            measure_mid.extend(segno)

        else:
            # Addition of segno and then of codas at the end of the intermediate measure
            measure_mid.extend(segno)
            measure_mid.extend(coda)
        # print(measure_mid)

        return measure_mid

    def create_final_sequence(self, measure_mid):
        """Function that create the final list measure using the intermediate mesure list

        Args:
            measure_mid (list): list of different jump in the measure sequences

        Returns:
            list: final mesure list
        """

        active_mesure = 1
        pairs_idx = 0
        measure_final = []

        # ? Maybe refactor this to be less complex
        # Go to (+2) if the last one number of the mesure has to trigger a jump
        while active_mesure < (self.total_number_of_measures + 2):

            if len(measure_mid) != pairs_idx:  # Check if there are still jumps to be made
                # Check if this measure has a jump to do
                if active_mesure == measure_mid[pairs_idx][0]:
                    measure_final.append(active_mesure)
                    active_mesure = measure_mid[pairs_idx][1]  # Do the jump

                    # Check if BRS (backward -> forward ... ending_one -> ending_two)
                    if len(measure_mid[pairs_idx]) == 4:
                        # Fill the gap between forward -> ending_one
                        for k in range(measure_mid[pairs_idx][1], (measure_mid[pairs_idx][2]+1)):
                            measure_final.append(k)
                        # Do the second jump
                        active_mesure = measure_mid[pairs_idx][3]

                    else:
                        measure_final.append(active_mesure)
                        active_mesure += 1
                    pairs_idx += 1

                else:
                    measure_final.append(active_mesure)
                    active_mesure += 1

            else:
                measure_final.append(active_mesure)
                active_mesure += 1

        # Delete the measure > to the max number
        measure_final.remove(self.total_number_of_measures + 1)
        return measure_final

    def create_symbole(self, start, end):
        """Function that preprocess and create pairs

        Args:
            start (list): list of starting point
            end (list): list of ending point

        Returns:
            list: list of pair compose by start first then end
        """

        if len(start) != 0 or len(end) != 0:  # Preprocessing pairs
            start, end = self.preprocess_len(start, end)

        # Symbol creation
        symbole = []
        for i, val in enumerate(start):
            symbole.append([val, end[i]])

        return symbole

    def preprocess_len(self, start, end):
        """Function that preprocess using the length of start and end lists

        Args:
            start (list): list of starting point
            end (list): list of ending point

        Returns:
            list: list of starting point equal to the ending one
            list : list of ending point equal to the starting one
        """

        # Equalize the sizes of the start and end lists
        while len(start) != len(end):

            if len(start) > len(end):
                start.pop()

            else:
                end.pop()

        return start, end

    def preprocess_br(self, brs, ending):
        """Function that preprocess BRC sorting and resizing ending to match with BRS

        Args:
            brs (list): list of BRS pairs [start,end]
            ending (list): list of ending pairs [start,end]

        Returns:
            list: list of BRS pairs [start,end]
            list: list of ending pairs [start,end]
        """
        while len(ending) > len(brs):
            ending.pop()

        for i in brs:
            if i[0] < i[1]:
                brs.remove(i)

        for i in ending:
            if i[0] > i[1]:
                ending.remove(i)

        return brs, ending

    def preprocess_coda(self, dacapo, segno, coda):
        """Function that preprocess coda using segno's length and dacapo's length 
        and delete incoherent pairs of segno and coda

        Args:
            dacapo (list): list of dacapo pairs
            segno (list): list of segno pairs
            coda (list): list of coda pairs

        Returns:
            list: list of segno pairs after deleting incoherent pairs
            list: list of coda pairs after deleting incoherent pairs
        """

        if (len(dacapo) + len(segno)) == 0:
            coda = []

        for i in segno:
            if i[0] < i[1]:
                segno.remove(i)

        for i in coda:
            if i[0] > i[1]:
                coda.remove(i)

        return segno, coda

    def preprocess_out_of_range(self, jump_list):
        """Function that preprocess measure mid using total number of measure
        if a jumps as a measure jump superior at the max one enter it 

        Args:
            jump_list (list): list of jump that have to be done on final measure

        Returns:
            list: list of jump that have to be done on final measure without measure 
            jump superior at the max one
        """
        element_to_delete = []
        for element_placement, val in enumerate(jump_list):
            if val[0] > self.total_number_of_measures or val[1] > self.total_number_of_measures:
                element_to_delete.insert(0, element_placement)

        for element_placement_to_delete in element_to_delete:
            del jump_list[element_placement_to_delete]

        return jump_list

    def create_dacapo(self, start):
        """Function that create DACAPO pairs using DACAPO's start and 1 that is the define end

        Args:
            start (list): list of the dacapo starts mesures

        Returns:
            list: list of dacapo pairs [start,end]
        """

        symbole = []
        for i in start:
            symbole.append([i, 1])

        return symbole

    def create_brc(self, brs, ending):
        """Function that create correct BRC on matching BRS with the good one ending

        Args:
            brs (list): list of BRS pairs
            ending (list): list of ending pairs

        Returns:
            list: list of BRC
            list: list of BRS
        """

        brc = []

        for end in ending:

            for i, brs_table in enumerate(brs):

                if end[0] >= brs_table[1]:

                    if i+1 == len(brs):
                        brc.append(
                            [brs_table[0], brs_table[1], end[0], end[1]])
                        brs.remove(brs_table)
                        break

                    elif end[1] <= brs[i+1][0]:
                        brc.append(
                            [brs_table[0], brs_table[1], end[0], end[1]])
                        brs.remove(brs_table)
                        break

        return brc, brs


def parse_args():  # Add the name of the file at the end of the command line
    """Function that add the name of the file at the end of the command line 
    that running the script

    Returns:
        string: name of the file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        type=str,
        help="Json path",
    )

    return parser.parse_args()


def main():
    # Json import and required information load
    args = parse_args()
    content = json.load(open(args.path))
    measure_list = content['lists']
    total_number_of_measures = content['total_number_of_measures']

    # Creation of the measurement object
    measure = MeasuresList(measure_list, total_number_of_measures)

    # Gathering the final measure
    measure_final = measure.measure_final

    try:
        # If measure_sequence key is not defined, it should raise an exception and skip to the except block
        final_mesure_validation = content['measure_sequence']
        print(measure_final == final_mesure_validation)
        # print(measure_final)

    except:
        #print("measure_final", measure_final)
        data = {'measure_final':  measure_final}

        out_path = args.path.replace('.json', '.out.json')
        with open(out_path, 'w') as f:
            json.dump(data, f)


if __name__ == "__main__":
    main()
