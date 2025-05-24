# suave_uploader.py
import requests
import io

def upload_to_suave(df, survey_name, user, password, referer, dzc_file=None):
    """
    Upload a DataFrame to SuAVE as a new survey.

    Parameters:
    - df: pandas.DataFrame to upload
    - survey_name: name for the new survey (without .csv)
    - user: SuAVE username
    - password: SuAVE password
    - referer: base URL of the SuAVE instance (e.g., 'https://suave-net.sdsc.edu/')
    - dzc_file: optional deep zoom config string

    Returns:
    - (success_flag: bool, message: str, new_survey_url: str or None)
    """
    s = requests.Session()
    headers = {
        "User-Agent": "suave user agent",
        "referer": referer
    }

    login_response = s.post(
        referer,
        headers=headers,
        data={
            "user": user,
            "pass": password,
            "remember-me": "true"
        }
    )

    if login_response.status_code != 200:
        return False, "Login failed. Please check your credentials.", None

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    files = {
        "file": (f"{survey_name}.csv", csv_buffer.getvalue())
    }
    data = {
        "name": survey_name,
        "user": user
    }
    if dzc_file:
        data["dzc"] = dzc_file

    upload_url = referer + "uploadCSV"
    upload_response = s.post(upload_url, files=files, data=data, headers=headers)

    if upload_response.status_code == 200:
        survey_url = f"{referer}main/file={user}_{survey_name}.csv"
        return True, "Upload successful.", survey_url
    else:
        return False, f"Upload failed ({upload_response.status_code} — {upload_response.reason})", None
