import dropbox
import os
import click
from src.util import stopwatch


def get_folder_files(client_id:str, client_secret:str, refresh_token:str, folder:str):

    dbx = dropbox.Dropbox(
            app_key = client_id,
            app_secret = client_secret,
            oauth2_refresh_token = refresh_token
        )
    
    listing = list_folder(dbx, folder, "")
    return listing

def get_file_data(client_id:str, client_secret:str, refresh_token:str, folder:str, subfolder:str, name:str):

    dbx = dropbox.Dropbox(
            app_key = client_id,
            app_secret = client_secret,
            oauth2_refresh_token = refresh_token
        )
    
    file = download(dbx=dbx, folder=folder, subfolder=subfolder, name=name)
    return file


#def generate_refresh_token(code:str, ):
    # curl --location --request POST 'https://api.dropboxapi.com/oauth2/token' \
    # -u '<APP_KEY>:<APP_SECRET>'
    # -H 'Content-Type: application/x-www-form-urlencoded' \
    # --data-urlencode 'code=<ACCESS_CODE>' \
    # --data-urlencode 'grant_type=authorization_code'

def list_folder(dbx, folder, subfolder):
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

def download(dbx, folder, subfolder, name):
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
    #print(len(data), 'bytes; md:', md)
    return data