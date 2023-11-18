"""
Interact with your dropbox account
"""
import os
import dropbox
import click

class DropBox:
    """
    Interact with your dropbox account
    """

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    def get_folder_files(self, folder:str):
        """List a folder.
        Return a dict mapping unicode filenames to
        FileMetadata|FolderMetadata entries.
        """

        dbx = dropbox.Dropbox(
                app_key = self.client_id,
                app_secret = self.client_secret,
                oauth2_refresh_token = self.refresh_token
            )

        listing = self.list_folder(dbx, folder, "")
        return listing

    def get_file_data(self, folder:str, subfolder:str, name:str):
        """
        Get a file from the folder/subfolder passed
        Return a byte array of the files contents.
        """

        dbx = dropbox.Dropbox(
                app_key = self.client_id,
                app_secret = self.client_secret,
                oauth2_refresh_token = self.refresh_token
            )

        file = self.download(dbx=dbx, folder=folder, subfolder=subfolder, name=name)
        return file


    def list_folder(self, dbx, folder, subfolder):
        """List a folder.
        Return a dict mapping unicode filenames to
        FileMetadata|FolderMetadata entries.
        """
        path = '/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
        while '//' in path:
            path = path.replace('//', '/')
        path = path.rstrip('/')
        try:
            #with stopwatch('list_folder'):
            res = dbx.files_list_folder(path)
        except dropbox.exceptions.ApiError as err:
            click.echo('Folder listing failed for', path, '-- assumed empty:', err)
            return {}
        except Exception as e:
            click.echo(e)
            return {}

        rv = {}
        for entry in res.entries:
            rv[entry.name] = entry
        return rv

    def download(self, dbx, folder, subfolder, name):
        """Download a file.
        Return the bytes of the file, or None if it doesn't exist.
        """
        path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        while '//' in path:
            path = path.replace('//', '/')
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
        data = res.content
        return data
    