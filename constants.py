
import re

no_special_character_regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
valid_email_regex = re.compile('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$')
# 8 characters length, 1 letter in upper case, 1 special character, 1 numeral, 1 letter in lower case
strong_password_regex = re.compile(
    '^(?=.*[A-Z])(?=.*[@_!#$%^&*()<>?/\|}{~:])(?=.*[0-9])(?=.*[a-z]).{8}$')
