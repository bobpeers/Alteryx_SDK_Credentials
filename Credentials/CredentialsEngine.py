import AlteryxPythonSDK as Sdk
import xml.etree.ElementTree as Et
from typing import NamedTuple, Optional
import ctypes as ct
import ctypes.wintypes as wt
from enum import Enum

"""
Access windows credentials

Credentials must be stored in the Windows Credentials Manager in the Control
Panel. This helper will search for "generic credentials" under the section
"Windows Credentials"

Example usage::

    result = get_generic_credential('foobar')
    if result:
        print("NAME:", result.username)
        print("PASSWORD:", result.password)
    else:
        print('No matching credentials found')

Based on https://gist.github.com/mrh1997/717b14f5783b49ca14310419fa7f03f6
"""

LPBYTE = ct.POINTER(wt.BYTE)

Credential = NamedTuple('Credential', [
    ('username', str),
    ('password', str)
])


def as_pointer(cls):
    """
    Class decorator which converts the class to ta ctypes pointer

    :param cls: The class to decorate
    :return: The class as pointer
    """
    output = ct.POINTER(cls)
    return output


class CredType(Enum):
    """
    Enumeration for different credential types.

    See https://docs.microsoft.com/en-us/windows/desktop/api/wincred/ns-wincred-_credentiala
    """
    GENERIC = 0x01
    DOMAIN_PASSWORD = 0x02
    DOMAIN_CERTIFICATE = 0x03
    DOMAIN_VISIBLE_PASSWORD = 0x04
    GENERIC_CERTIFICATE = 0x05
    DOMAIN_EXTENDED = 0x06
    MAXIMUM = 0x07
    MAXIMUM_EX = MAXIMUM + 1000


@as_pointer
class CredentialAttribute(ct.Structure):
    _fields_ = [
        ('Keyword', wt.LPWSTR),
        ('Flags', wt.DWORD),
        ('ValueSize', wt.DWORD),
        ('Value', LPBYTE)]


@as_pointer
class WinCredential(ct.Structure):
    _fields_ = [
        ('Flags', wt.DWORD),
        ('Type', wt.DWORD),
        ('TargetName', wt.LPWSTR),
        ('Comment', wt.LPWSTR),
        ('LastWritten', wt.FILETIME),
        ('CredentialBlobSize', wt.DWORD),
        ('CredentialBlob', LPBYTE),
        ('Persist', wt.DWORD),
        ('AttributeCount', wt.DWORD),
        ('Attributes', CredentialAttribute),
        ('TargetAlias', wt.LPWSTR),
        ('UserName', wt.LPWSTR)]


def get_generic_credential(name: str) -> Optional[Credential]:
    """
    Returns a tuple of name and password of a generic Windows credential.

    If no matching credential is found, this will return ``None``

    :param name: The lookup string for the credential.
    """
    advapi32 = ct.WinDLL('Advapi32.dll')
    advapi32.CredReadA.restype = wt.BOOL
    advapi32.CredReadA.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, WinCredential]

    cred_ptr = WinCredential()
    try:
        if advapi32.CredReadW(name, CredType.GENERIC.value, 0, ct.byref(cred_ptr)):
            username = cred_ptr.contents.UserName
            cred_blob = cred_ptr.contents.CredentialBlob
            cred_blob_size = cred_ptr.contents.CredentialBlobSize
            password_as_list = [int.from_bytes(cred_blob[pos:pos+2], 'little')
                                for pos in range(0, cred_blob_size, 2)]
            password = ''.join(map(chr, password_as_list))
            advapi32.CredFree(cred_ptr)
            return Credential(username, password)
    except ValueError:
        return None
    else:
        return None

class AyxPlugin:
    def __init__(self, n_tool_id: int, alteryx_engine: object, output_anchor_mgr: object):
        # Default properties
        self.n_tool_id: int = n_tool_id
        self.alteryx_engine: Sdk.AlteryxEngine = alteryx_engine
        self.output_anchor_mgr: Sdk.OutputAnchorManager = output_anchor_mgr

        pass

    def pi_init(self, str_xml: str):
        self.output_anchor = self.output_anchor_mgr.get_output_anchor('Output')
        self.credential_name = Et.fromstring(str_xml).find('credential_name').text if 'credential_name' in str_xml else None

        if self.credential_name is None:
            self.display_error_msg('Generic Credential name cannot be empty.')
            return False
        pass

    def pi_add_incoming_connection(self, str_type: str, str_name: str) -> object:
        return self

    def pi_add_outgoing_connection(self, str_name: str) -> bool:
        return True

    def build_record_info_out(self):
        """
        A non-interface helper for pi_push_all_records() responsible for creating the outgoing record layout.
        :param file_reader: The name for csv file reader.
        :return: The outgoing record layout, otherwise nothing.
        """

        record_info_out = Sdk.RecordInfo(self.alteryx_engine)  # A fresh record info object for outgoing records.
        #We are returning a single column and a single row. 
        
        record_info_out.add_field('Username', Sdk.FieldType.string, 100)
        record_info_out.add_field('Password', Sdk.FieldType.string, 100)
        return record_info_out

    def pi_push_all_records(self, n_record_limit: int) -> bool:
        record_info_out = self.build_record_info_out()  # Building out the outgoing record layout.
        self.output_anchor.init(record_info_out)  # Lets the downstream tools know of the outgoing record metadata.
        record_creator = record_info_out.construct_record_creator()  # Creating a new record_creator for the new data.

        result = get_generic_credential(self.credential_name)

        if result:
            record_info_out[0].set_from_string(record_creator, result.username)
            record_info_out[1].set_from_string(record_creator, result.password)
            self.display_info(f'Retrieved credential for {self.credential_name}')
        else:
            self.display_error_msg(f'Generic credential {self.credential_name} does not exist or cannot be retrieved')

        out_record = record_creator.finalize_record()
        self.output_anchor.push_record(out_record, False)  # False: completed connections will automatically close.
        record_creator.reset()  # Resets the variable length data to 0 bytes (default) to prevent unexpected results.

        self.output_anchor.close()  # Close outgoing connections.
        return True

    def pi_close(self, b_has_errors: bool):
        self.output_anchor.assert_close()  # Checks whether connections were properly closed.

    def display_error_msg(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.error, msg_string)

    def display_info(self, msg_string: str):
        self.alteryx_engine.output_message(self.n_tool_id, Sdk.EngineMessageType.info, msg_string)


class IncomingInterface:
    def __init__(self, parent: AyxPlugin):
        pass

    def ii_init(self, record_info_in: Sdk.RecordInfo) -> bool:
        pass
   
    def ii_push_record(self, in_record: Sdk.RecordRef) -> bool:
        pass

    def ii_update_progress(self, d_percent: float):
        # Inform the Alteryx engine of the tool's progress.
        pass


    def ii_close(self):
        pass
