import re

from utils import (FORMAT_1_OPCODE, FORMAT_2_OPCODE, FORMAT_3_OPCODE,
                   OPCODE, REGISTER, SEVEN_SEGMENT_DISPLAY, TRAFFIC_LIGHT,
                   convert_to_hex, hex_to_binary)

RAM = ['00' for i in range(4096)]


def get_opcode_key(val):
    for key, value in OPCODE.items():
        if val == value:
            return key
    return None


class MicroSim:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_ram_loaded = False
        self.decoded_micro_instructions = []
        self.index = 0
        self.is_running = True
        self.prev_index = -1
        self.counter = 0

    def read_obj_file(self, filename):
        file = open(filename, 'r')
        lines = file.readlines()
        i = 0
        for line in lines:
            line.strip()
            hex_instruction = ''.join(line.split())
            RAM[i] = hex_instruction[0:2]
            RAM[i + 1] = hex_instruction[2:]
            i += 2
        self.is_ram_loaded = True
        lines.clear()
        file.close()


    def disassembled_instruction(self):

        instruction = hex_to_binary(f'{RAM[self.index]}{RAM[self.index + 1]}')

        opcode = get_opcode_key(instruction[0:5])
        register_a = ''
        register_b = ''
        register_c = ''
        dis_instruction = ''

        if opcode in FORMAT_1_OPCODE:

            ra = f'R{int(instruction[5:8], 2)}'
            rb = f'R{int(instruction[8:11], 2)}'
            rc = f'R{int(instruction[11:14], 2)}'

            register_a = f' {ra}'
            register_b = f' {rb}'
            register_c = f' {rc}'

            if register_c != ' R0':
                dis_instruction = opcode + register_a + ',' + register_b + ',' + register_c
            else:
                dis_instruction = opcode + register_a + ',' + register_b

        elif opcode in FORMAT_2_OPCODE:

            ra = f'R{int(instruction[5:8], 2)}'
            address_or_const = f'{int(instruction[8:], 2):02x}'

            register_a = f' {ra}'

            if register_a != ' R0':
                dis_instruction = opcode + register_a + ', ' + address_or_const
            else:
                dis_instruction = opcode + ' ' + address_or_const

        elif opcode in FORMAT_3_OPCODE:
            ra = f'R{int(instruction[5:8], 2)}'
            address = f'{int(instruction[5:], 2):02x}'

            register_a = f' {ra}'

            if register_a != ' R0':
                dis_instruction = opcode + register_a + ', ' + address
            else:
                dis_instruction = opcode + ' ' + address

        return dis_instruction

    def run_micro_instructions(self):
        REGISTER['ir'] = f'{RAM[self.index]}{RAM[self.index + 1]}'
        binary_instruction = hex_to_binary(
            f'{RAM[self.index]}{RAM[self.index + 1]}')
        self.execute_instruction(binary_instruction)

    def run_micro_instructions_step(self, step_index):

        REGISTER['ir'] = f'{RAM[self.index]}{RAM[self.index + 1]}'
        binary_instruction = hex_to_binary(
            f'{RAM[self.index]}{RAM[self.index + 1]}')
        self.execute_instruction(binary_instruction)
        if self.prev_index == self.index:
            self.is_running = False
        else:
            self.prev_index = self.index

    def traffic_lights_binary(self):
        return hex_to_binary(f'{RAM[TRAFFIC_LIGHT["port"]]}')

    def seven_segment_binary(self):

        return hex_to_binary(f'{RAM[SEVEN_SEGMENT_DISPLAY["port"]]}')

    def micro_clear(self):
        self.is_ram_loaded = False
        self.decoded_micro_instructions = []
        self.index = 0
        self.is_running = True
        self.prev_index = -1
        self.counter = 0
        for m in range(4096):
            RAM[m] = '00'

        for k, v in REGISTER.items():
            if k == 'pc' or k == 'sp':
                REGISTER[k] = f'{0:03x}'
            elif k == 'ir':
                REGISTER[k] = f'{0:04x}'
            elif k == 'cond':
                REGISTER[k] = f'{0:01x}'
            else:
                REGISTER[k] = f'{0:02x}'

    def execute_instruction(self, instruction):
        if re.match('^[0]+$', instruction):
            pass
        else:

            opcode = get_opcode_key(instruction[0:5])

            if opcode in FORMAT_1_OPCODE:
                ra = f'R{int(instruction[5:8], 2)}'
                rb = f'R{int(instruction[8:11], 2)}'
                rc = f'R{int(instruction[11:14], 2)}'
                if opcode == 'loadrind':
                    REGISTER[ra.lower()] = RAM[int(REGISTER[rb.lower()], 16)]
                elif opcode == 'storerind':
                    REGISTER[rb.lower()] = RAM[int(REGISTER[ra.lower()], 16)]
                elif opcode == 'grt':
                    REGISTER['cond'] = str(int(REGISTER[ra.lower()] > REGISTER[rb.lower()]))
                elif opcode == 'add':
                    REGISTER[ra.lower()] = convert_to_hex(int(REGISTER[rb.lower()], 16) + int(REGISTER[rc.lower()], 16),
                                                          8)
                elif opcode == 'sub':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(REGISTER[rb.lower()], 16) - int(REGISTER[rc.lower()], 16), 8)
                elif opcode == 'and':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(REGISTER[rb.lower()], 16) * int(REGISTER[rc.lower()], 16), 8)
                elif opcode == 'or':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(REGISTER[rb.lower()], 16) + int(REGISTER[rc.lower()], 16), 8)
                elif opcode == 'xor':
                    _xor = int(REGISTER[rb.lower()], 16) + int(REGISTER[rc.lower()], 16) - \
                           2 * int(REGISTER[rb.lower()], 16) * int(REGISTER[rc.lower()], 16)
                    REGISTER[ra.lower()] = convert_to_hex(_xor, 8)
                elif opcode == 'not':
                    REGISTER[ra.lower()] = convert_to_hex(
                        self.bit_not(hex_to_binary(REGISTER[rb.lower()])), 8)
                elif opcode == 'neg':
                    REGISTER[ra.lower()] = convert_to_hex(
                        (-1) * int(REGISTER[rb.lower()], 16), 8)
                elif opcode == 'shiftr':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(REGISTER[rb.lower()], 16) >> int(REGISTER[rc.lower()], 16), 8)
                elif opcode == 'shiftl':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(REGISTER[rb.lower()], 16) << int(REGISTER[rc.lower()], 16), 8)
                elif opcode == 'rotar':
                    _rotar = self.rotr(int(REGISTER[rb.lower()], 16), int(
                        REGISTER[rc.lower()], 16))
                    REGISTER[ra.lower()] = convert_to_hex(_rotar, 8)
                elif opcode == 'rotal':
                    _rotl = self.rotl(int(REGISTER[rb.lower()], 16), int(
                        REGISTER[rc.lower()], 16))
                    REGISTER[ra.lower()] = convert_to_hex(_rotl, 8)
                elif opcode == 'jmprind':
                    self.program_counter = int(REGISTER[ra.lower()], 16)
                elif opcode == 'grteq':
                    REGISTER['cond'] = str(int(int(REGISTER[ra.lower()], 16) >= int(
                        REGISTER[rb.lower()], 16)))
                elif opcode == 'eq':
                    REGISTER['cond'] = str(int(int(REGISTER[ra.lower()], 16) == int(
                        REGISTER[rb.lower()], 16)))
                elif opcode == 'neq':
                    REGISTER['cond'] = str(int(int(REGISTER[ra.lower()], 16) != int(
                        REGISTER[rb.lower()], 16)))
                elif opcode == 'nop':
                    # Do nothing
                    pass
                self.index += 2
                REGISTER['pc'] = convert_to_hex(
                    int(REGISTER['pc'], 16) + 2, 12)
            elif opcode in FORMAT_2_OPCODE:
                ra = f'R{int(instruction[5:8], 2)}'
                address_or_const = int(instruction[8:], 2)
                if opcode == 'load' or 'loadim':
                    REGISTER[ra.lower()] = convert_to_hex(
                        int(RAM[address_or_const] + RAM[address_or_const + 1], 16), 8)
                elif opcode == 'store':
                    RAM[self.index] = REGISTER[ra.lower()]
                elif opcode == 'addim':
                    _addim = int(
                        REGISTER[ra], 16) + int(RAM[address_or_const] + RAM[address_or_const + 1], 16)
                    REGISTER[ra] = convert_to_hex(_addim, 8)
                elif opcode == 'subim':
                    _subim = int(
                        REGISTER[ra], 16) - int(RAM[address_or_const] + RAM[address_or_const + 1], 16)
                    REGISTER[ra] = convert_to_hex(_subim, 8)
                elif opcode == 'pop':
                    REGISTER[ra.lower()] = RAM[REGISTER['sp']]
                    REGISTER['sp'] = convert_to_hex(
                        int(REGISTER['sp'], 16) + 1, 12)
                elif opcode == 'push':
                    REGISTER['sp'] = convert_to_hex(
                        int(REGISTER['sp'], 16) - 1, 12)
                    RAM[REGISTER['sp']] = REGISTER[ra.lower()]
                elif opcode == 'loop':
                    reg_ra = int(REGISTER[ra.lower()], 16) - 1
                    REGISTER[ra.lower()] = convert_to_hex(reg_ra, 8)
                    if reg_ra != 0:
                        REGISTER['sp'] = convert_to_hex(address_or_const, 12)
                self.index += 2
                REGISTER['pc'] = convert_to_hex(
                    int(REGISTER['pc'], 16) + 2, 12)
            elif opcode in FORMAT_3_OPCODE:
                ra = f'R{int(instruction[5:8], 2)}'
                address = int(instruction[5:], 2)
                if opcode == 'jmpaddr':
                    self.index = address
                    REGISTER['pc'] = convert_to_hex(address, 12)
                elif opcode == 'jcondrin':
                    REGISTER['pc'] = REGISTER[ra.lower()] if int(REGISTER['cond']) else convert_to_hex(
                        int(REGISTER['pc'], 16) + 2,
                        12)
                elif opcode == 'jcondaddr':
                    REGISTER['pc'] = convert_to_hex(address, 3) if int(REGISTER['cond']) else convert_to_hex(
                        int(REGISTER['pc'], 16) + 2, 12)
                elif opcode == 'call':
                    REGISTER['sp'] = convert_to_hex(
                        int(REGISTER['sp'], 16), 12)
                    RAM[REGISTER['sp']] = REGISTER['pc']
                    REGISTER['pc'] = f'{address + 2:03x}'
            elif opcode == 'return':
                REGISTER['pc'] = RAM[REGISTER['sp']]
                REGISTER['sp'] = f"{int(REGISTER['sp'], 16) + 2:03x}"

    def bit_not(self, n, numbits=8):
        return (1 << numbits) - 1 - n

    def rotl(self, num, bits):
        bit = num & (1 << (bits - 1))
        num <<= 1
        if bit:
            num |= 1
        num &= (2 << bits - 1)

        return num

    def rotr(self, num, bits):
        num &= (2 << bits - 1)
        bit = num & 1
        num >>= 1
        if bit:
            num |= (1 << (bits - 1))

        return num
