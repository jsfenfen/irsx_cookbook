from irsx.xmlrunner import XMLRunner
from datetime import datetime
from logging import getLogger

logger = getLogger('return')


def combine_fields(value1, value2):
    '''Returns the sum of value1 and value2 or whichever operand is not None. Returns None when both are None.'''
    if value1 is not None and value2 is not None:
        return value1 + value2
    elif value1 is None:
        return value2
    elif value2 is None:
        return value1
    else:
        return None


'''The Return class represents shared attributes across all 990 forms. In general, these are values found in IRSx's ReturnHeader990x schedule.'''
class Return:
    def flatten_atts_for_db(self):
        '''
        Returns a flattened list of dictionaries populated with return header, balance, comp information for each person.
        '''
        # obj_tbl_field_map is a dictionary that maps object key names (ex: self.header_dict['ein']) to preferred field names on any output
        # flatten_atts_for_db() searches self.obj_tbl_field_map for user-defined custom keys before falling back to class' default keys
        db_rows = []
        for person in self.people:
            procd_person = {}
            for k, v in person.items():
                try:
                    k = self.obj_tbl_field_map[k]
                except (KeyError, TypeError) as e:
                    # logger.debug(e)
                    pass
                procd_person[k] = v
            for k, v in self.balance_dict.items():
                try:
                    k = self.obj_tbl_field_map[k]
                except (KeyError, TypeError) as e:
                    # logger.debug(e)
                    pass
                procd_person[k] = v
            for k, v in self.header_dict.items():
                try:
                    k = self.obj_tbl_field_map[k]
                except (KeyError, TypeError) as e:
                    # logger.debug(e)
                    pass
                procd_person[k] = v
            procd_person['object_id'] = self.object_id
            db_rows.append(procd_person)

        return db_rows

    def process_header_fields(self):
        '''
        Process header information from ReturnHeader990x and return it to __init__ as a dict
        Header information will be handled the same across all forms of the 990
        '''
        header = self.xml_runner.run_sked(self.object_id, 'ReturnHeader990x')
        results = header.get_result()[0]
        header_values = results['schedule_parts']['returnheader990x_part_i']

        header_dict = {}

        header_obj_irsx_map = {
            'ein': 'ein',
            'state': 'USAddrss_SttAbbrvtnCd',
            'city': 'USAddrss_CtyNm',
            'tax_year': 'RtrnHdr_TxYr',
            'org': 'BsnssNm_BsnssNmLn1Txt',
            # custom_key_name: IRSX_key_name
            # add valid ReturnHeader990x keys here to save those values during processing (see variables.csv)
        }

        obj_str_handling_map = {
            'state': lambda x: x.upper(),
            'city': lambda x: x.title(),
            'org': lambda x: x.title()
            # map custom keys to string handling lambdas for quick & dirty cleaning

        }

        for obj_key, irsx_key in header_obj_irsx_map.items():
            try:
                value = header_values[irsx_key]
                if obj_key in obj_str_handling_map:
                    value = obj_str_handling_map[obj_key](value)
                header_dict[obj_key] = value
            except KeyError:
                header_dict[obj_key] = None

        # special case: fiscal year date
        try:
            tax_prd_end_date = header_values['RtrnHdr_TxPrdEndDt']
            tax_prd_end_date =  datetime.strptime(tax_prd_end_date, '%Y-%m-%d')
            header_dict['fiscal_year'] = tax_prd_end_date.year
        except KeyError:
            header_dict['fiscal_year'] = None

        try:
            header_dict['dba'] = header_values['BsnssNm_BsnssNmLn1Txt']
        except KeyError:
            header_dict['dba'] = None

        return header_dict

    def process_compensation_fields(self):
        '''Compensation fields are specific to the flavor of 990 and this is implemented on child classes.'''
        raise NotImplementedError

    def process_balance_fields(self):
        '''Balance fields are specific to the flavor of 990 and this is implemented on child classes.'''
        raise NotImplementedError

    def __init__(self, object_id, obj_tbl_field_map=None):
        self.object_id = object_id
        self.xml_runner = XMLRunner()
        self.obj_tbl_field_map = obj_tbl_field_map

        self.header_dict = self.process_header_fields()
        self.balance_dict = self.process_balance_fields()
        self.people = self.process_compensation_fields()

        self.failures = {
            'comp': True if self.people is None else False,
            'balance': True if self.balance_dict is None else False,
            'header': True if self.header_dict is None else False
        }


    def __repr__(self):
        return '''Object_ID: {object_id}\nHeader: {header}\nBalance: {balance}\nPeople: {people}\n'''.format(
            object_id=self.object_id,
            header=self.header_dict,
            balance=self.balance_dict,
            people=self.people
        )



'''This child class represents information we're pulling from the 990EO'''
class Return_990(Return):
    def process_compensation_fields(self):
        db_irsx_key_map = {
                 'person': 'PrsnNm',
                 'title': 'TtlTxt',
                 'base_org': 'BsCmpnstnFlngOrgAmt',
                 'base_rel': 'CmpnstnBsdOnRltdOrgsAmt',
                 'bonus_org': 'BnsFlngOrgnztnAmnt',
                 'bonus_rel': 'BnsRltdOrgnztnsAmt',
                 'other_org': 'OthrCmpnstnFlngOrgAmt',
                 'other_rel': 'OthrCmpnstnRltdOrgsAmt',
                 'defer_org': 'DfrrdCmpnstnFlngOrgAmt',
                 'defer_rel': 'DfrrdCmpRltdOrgsAmt',
                 'nontax_ben_org': 'NntxblBnftsFlngOrgAmt',
                 'nontax_ben_rel': 'NntxblBnftsRltdOrgsAmt',
                 '990_total_org': 'TtlCmpnstnFlngOrgAmt',
                 '990_total_rel': 'TtlCmpnstnRltdOrgsAmt',
                 'prev_rep_org': 'CmpRprtPrr990FlngOrgAmt',
                 'prev_rep_rel': 'CmpRprtPrr990RltdOrgsAmt'
                # custom_key_name: IRSX_key_name
                # add valid Schedule J IRSX key names here to save those values during processing (see variables.csv)
             }

        db_type_map = {
            # Key your custom keys to types to specify how each key should be cast on processing
            key: int for key in db_irsx_key_map
        }

        obj_str_handling_map = {
            # Key custom keys to lambda functions for quick and dirty cleaning on those values
            'person': lambda x: x.title(),
            'title': lambda x: x.title()
        }

        db_type_map['person'] = str
        db_type_map['title'] = str

        sked_j = self.xml_runner.run_sked(self.object_id, 'IRS990ScheduleJ')
        results = sked_j.get_result()[0]
        try:
            sked_j_values = results['groups']['SkdJRltdOrgOffcrTrstKyEmpl']
        except KeyError:
            return None

        people = []

        for employee_dict in sked_j_values:
            processed = {}
            for db_key in db_irsx_key_map:
                irsx_key = db_irsx_key_map[db_key]
                db_type = db_type_map[db_key]
                try:
                    value = db_type(employee_dict[irsx_key]) if irsx_key in employee_dict else None
                    if value is None and irsx_key == 'PrsnNm':
                        # sometimes people's names show up under BsnssNmLn1Txt
                        alt_person_key = 'BsnssNmLn1Txt'
                        value = employee_dict[alt_person_key] if alt_person_key in employee_dict.keys() else None
                    if db_key in obj_str_handling_map:
                        value = obj_str_handling_map[db_key](value)
                    processed[db_key] = value
                except TypeError:
                    # if we can't cast the value we set it to None
                    processed[db_key] = None
                except AttributeError:
                    processed[db_key] = None
            person_name = processed['person']

            people.append(processed)

        return people

    def process_balance_fields(self):
        db_irsx_key_map = {
            'total_contrib': 'TtlCntrbtnsAmt',
            'govt_grants': 'GvrnmntGrntsAmt'
            # custom_key_name: IRSX_key_name
            # add valid Part 8 IRSX key names here to save those values during processing (see variables.csv)
        }

        balance = self.xml_runner.run_sked(self.object_id, 'IRS990')

        results = balance.get_result()[0]

        try:
            balance_values = results['schedule_parts']['part_viii']
        except KeyError:
            return None

        processed = {}
        for db_key in db_irsx_key_map:
            irsx_key = db_irsx_key_map[db_key]
            processed[db_key] = balance_values[irsx_key] if irsx_key in balance_values.keys() else None

            try:
                processed[db_key] = int(processed[db_key])
            except TypeError:
                processed[db_key] = None

        p = processed
        p['private_support'] = combine_fields(p['total_contrib'], p['govt_grants'])

        return processed


def main():
    example_object_id = 201711109349301001
    r = Return_990(example_object_id)
    print(r.flatten_atts_for_db())


if __name__ == '__main__':
    main()