import arcpy
import binascii
from datetime import datetime
import json
import os
import OpenSSL
from requests import Session
import shutil
import sys
from tkinter import *
from tkinter import simpledialog
from tkinter.filedialog import askopenfilename

# Local imports
sys.path.append(os.path.dirname(__file__))
from exceptions import PkiPasswordError

# Non-arcpy dependencies
from requests_pkcs12 import Pkcs12Adapter
import requests_pkcs12


class ArcPKI:
    """
    Catches user PKI certificate and password, storing 
    them for repeated use over a limited duration.
    """
    def __init__(self):

        self.config = Config()
        self.pki = self.config.pki
        self.ca = self.config.ca
        self.pki_pw_file = os.path.join(self.config.user_data_path, "p.pd")
        self.pki_pw = self._password()

    def _get_pki_pw(self):
        """
        Tkinter orchestration
        """
        root = Tk()
        root.geometry("200x200+700+500")
        root.update_idletasks()
        root.withdraw()
        pki_pw = self._pwbox(root)
        return pki_pw

    def _password(self):
        """
        Logic to decode or request user PKI pw
        """
        self._remove()  # Prompt for pw every 24 hours
        if not os.path.exists(self.pki_pw_file):
            pw = self._get_pki_pw()
            if not pw:
                raise PkiPasswordError("No PKI password provided.")
            # Write temp pw file
            with open(self.pki_pw_file, 'wb') as pki_pw:
                pki_pw.write(
                    binascii.hexlify(bytes(pw.encode("utf-8")))
                )
                return pw
        else:
            # Temp file exists and is less than 24 hours old; decode
            with open(self.pki_pw_file, 'rb') as pki_pw:
                pw_bin = pki_pw.readline()
                return str(binascii.unhexlify(pw_bin), "utf-8")

    def _pwbox(self, tkwin):
        """
        Simple password box, called by Tkinter
        """
        return simpledialog.askstring("PKI Password", "Enter PKI Password:\t\t\t\t\t", show="*", parent=tkwin)

    def _remove(self):
        """
        Cleans up temporary pw file
        """
        if os.path.exists(self.pki_pw_file):
            now = datetime.now()
            ctime = datetime.fromtimestamp(os.path.getctime(self.pki_pw_file))
            duration = now - ctime
            age_in_minutes = duration.total_seconds() / 60
            if age_in_minutes < 1440:
                return None
            else:
                arcpy.AddWarning("Your PKI password is more than 24 hours old; you must enter your password again.")
                try:
                    os.remove(self.pki_pw_file)
                    return True
                except OSError:
                    return False

    def get(self, url):
        """
        Returns raw response
        """
        try:
            timeout = (10, 15)
            return requests_pkcs12.get(
                url,
                pkcs12_filename=self.pki,
                pkcs12_password = self.pki_pw,
                verify=self.ca,
                timeout=timeout
            )
        except OpenSSL.crypto.Error as e:
            arcpy.AddWarning("Password incorrect. On next run, you will be prompted for your PKI password again.")
            os.remove(self.pki_pw_file)

    def geoaxis(self, auth_url):
        """
        An admittedly ghetto approach to dealing with geoaxis. Returns a
        Session object that can be used indefinitely against any geoaxis
        authenticated service.  Use actual service endpoint root as auth_url.
        """
        adapter = Pkcs12Adapter(
            pkcs12_filename=self.pki,
            pkcs12_password=self.pki_pw
        )
        s = Session()
        s.mount('https://', adapter)
        s.get(auth_url)
        return s

    def session_get(self, auth_url, urls:list, json=False):
        """
        Utility method to mount a Session and return a generator
        of responses given a list of urls.  Works with geoaxis
        services. Use service endpoint root as auth_url.
        """
        adapter = Pkcs12Adapter(
            pkcs12_filename=self.pki,
            pkcs12_password=self.pki_pw
        )
        s = Session()
        t = s.get(auth_url)
        for url in urls:
            r = s.get(url, timeout=50)
            if json:
                yield r.json()
            else:
                yield r


class Config:

    def __init__(self):
        
        self.user_data_path = os.path.join(os.path.expanduser('~'), ".arcpki")
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)
        self.pki_config_file = os.path.join(self.user_data_path, "pki_config.json")
        if not os.path.exists(self.pki_config_file):
            self.generate_config()
        user_settings = self.read_config(self.pki_config_file)
        self.pki = user_settings["USER_PKI"]
        self.ca = user_settings["VERIFY"]

    def _get_pki(self):
        """
        Requests the PKCS12 soft cert (.p12) from the user
        """
        root = Tk()
        root.withdraw()
        pki = str(askopenfilename(filetypes=[("PKCS12 Certificates", "*.p12")], title="Select Digital Signing Certificate (.p12)"))
        root.destroy()
        pki_name = os.path.split(pki)[1]
        copied_pki = os.path.join(self.user_data_path, pki_name)
        shutil.copyfile(pki, copied_pki)

        return copied_pki

    def _get_ca_chain(self):
        """
        Requests a certificate authority (CA) bundle
        """
        root = Tk()
        root.withdraw()
        ca_bundle = str(askopenfilename(filetypes=[("Certificate Authority", ".cer .crt .pem .pfx")], title="Select Certificate Authority Bundle"))
        root.destroy()
        ca_name = os.path.split(ca_bundle)[1]
        copied_ca = os.path.join(self.user_data_path, ca_name)
        shutil.copyfile(ca_bundle, copied_ca)

        return copied_ca

    def generate_config(self):
        config_file = os.path.join(self.user_data_path, "pki_config.json")
        data = json.dumps({
            "USER_PKI": self._get_pki(),
            "VERIFY": self._get_ca_chain()
        })
        
        with open(config_file, "w") as pki_config_out:
            pki_config_out.write(data)
            return True

    def read_config(self, config_file):
        with open(config_file, "r") as cf:
            return json.load(cf)


if __name__ == "__main__":

    arcpki = ArcPKI()
    r = arcpki.get("https://www.google.com")
        
