from lxml import etree
import os
import pandas as pd
from msgspec.json import decode
import shutil


class Defect:
    assemblyRevision = ''
    serialNumber = ''
    testerName = ''
    type = ''
    dataFolderName = ''
    indictmentType = ''
    repairOperator = ''
    repairStatus = ''
    designator = ''
    partId = ''
    pinId = ''

    def to_dict(self):
        res = {}
        res['assemblyRevision'] = self.assemblyRevision
        res['serialNumber'] = self.serialNumber
        res['testerName'] = self.testerName
        res['type'] = self.type
        res['dataFolderName'] = self.dataFolderName
        res['indictmentType'] = self.indictmentType
        res['repairOperator'] = self.repairOperator
        res['repairStatus'] = self.repairStatus
        res['designator'] = self.designator
        res['partId'] = self.partId
        res['pinId'] = self.pinId

        return res


def parse_file_for_defects(path, include_pin=True):
    root = etree.parse(path)
    ns = root.getroot().nsmap
    res = []  # Defect()
    serialNumber = root.getroot().find("ns1:BoardXML", ns).attrib.get('serialNumber')
    testerName = root.getroot().find("ns1:StationXML", ns).attrib.get('testerName')
    assemblyRevision = root.getroot().find("ns1:BoardXML", ns).attrib.get('assemblyRevision')
    dataFolderName = root.getroot().attrib.get('dataFolderName')

    # TestXML = root.getroot().findall(".//ns1:TestXML", ns)
    TestXML = root.getroot().findall(".//ns1:TestXML", ns)
    for test in TestXML:
        name = test.attrib.get('name')
        IndictmentXML = test.findall(".//ns1:IndictmentXML", ns)
        PinXML = test.findall(".//ns1:PinXML", ns)

        for Indictment in IndictmentXML:
            tmp = Defect()
            tmp.assemblyRevision = assemblyRevision
            tmp.serialNumber = serialNumber
            tmp.testerName = testerName
            tmp.designator = name
            tmp.dataFolderName = dataFolderName
            tmp.type = 'IndictmentXML'
            tmp.indictmentType = Indictment.attrib.get('indictmentType')
            tmp.repairOperator = Indictment.find("ns1:RepairActionXML", ns).attrib.get('repairOperator')
            tmp.repairStatus = Indictment.find("ns1:RepairActionXML", ns).attrib.get('repairStatus')
            tmp.partId = Indictment.find("ns1:ComponentXML", ns).attrib.get('partId')
            res.append(tmp)

        if include_pin:
            partId = IndictmentXML[0].find("ns1:ComponentXML", ns).attrib.get('partId')
            repairOperator = IndictmentXML[0].find("ns1:RepairActionXML", ns).attrib.get('repairOperator')
            for pin in PinXML:
                repairStatus = pin.attrib.get('repairStatus')
                id = pin.attrib.get('id')
                PinIndictmentXML = pin.findall(".//ns1:PinIndictmentXML", ns)
                tmp.dataFolderName = dataFolderName

                for pinIndictment in PinIndictmentXML:
                    tmp = Defect()
                    tmp.assemblyRevision = assemblyRevision
                    tmp.serialNumber = serialNumber
                    tmp.testerName = testerName
                    tmp.designator = name
                    tmp.dataFolderName = dataFolderName
                    tmp.type = 'PinXML'
                    tmp.indictmentType = pinIndictment.attrib.get('indictmentType')
                    tmp.repairOperator = repairOperator
                    tmp.repairStatus = repairStatus
                    tmp.partId = partId
                    tmp.pinId = id
                    res.append(tmp)

    return res


def get_dataFolderName(path):
    root = etree.parse(path)
    dataFolderName = root.getroot().attrib.get('dataFolderName')
    return dataFolderName


def get_df_defects(file_path, include_pin):
    defects = []
    tmp = parse_file_for_defects(file_path, include_pin=include_pin)
    for t in tmp:
        defects.append(t.to_dict())

    df_defects = pd.DataFrame(defects)

    return df_defects


def get_img_df(img_folder):
    path_json = img_folder + 'json_data.json'

    with open(path_json, "rb") as f:
        data = decode(f.read())

    all_rows = data['post_ticket']['call_summary']['falsecall_refdes']
    all_rows.update(data['post_ticket']['call_summary']['truecall_refdes'])

    df_js = pd.DataFrame.from_dict(all_rows, orient='index')
    df_js.reset_index(inplace=True)
    df_js.rename(columns={'index': 'designator'}, inplace=True)
    df_js['img_folder'] = img_folder
    df_js['img_path'] = df_js.apply(lambda row: img_folder + row.defect_image, axis=1)

    return df_js


def copy_img_files(xml_file: str, img_folder_path: str,
                   buffer_path: str, arch_xml: str, arch_img: str):
    img_folder_name = get_dataFolderName(xml_file)

    if img_folder_name is not None:
        Y = img_folder_name.split('-')[-6][-4:]
        M = img_folder_name.split('-')[-5]
        D = img_folder_name.split('-')[-4]
        curr_img_folder_path = img_folder_path + Y + '/' + M + '/' + D + '/' + img_folder_name + '/'
        list_df = []

        if os.path.isfile(curr_img_folder_path + 'json_data.json'):
            df_img_paths = [curr_img_folder_path + 'json_data.json']
            df_defects_tmp = get_df_defects(xml_file, False)
            df_img_tmp = get_img_df(curr_img_folder_path)
            df_total = df_defects_tmp.merge(df_img_tmp, on='designator', how='inner')
            list_df.append(df_total)

            df_total_pre = pd.concat(list_df)
            df_total_pre = df_total_pre[df_total_pre.defect_image != 'noImage']
            df_img_paths.extend(df_total_pre['img_path'].tolist())
            df_img_paths = list(set(df_img_paths))

            os.makedirs(buffer_path + '/' + img_folder_name, exist_ok=True)
            os.makedirs(arch_img + Y + '/' + M + '/' + D + '/' + img_folder_name, exist_ok=True)
            os.makedirs(arch_xml + Y + '/' + M + '/' + D, exist_ok=True)

        else:
            msg = 'No json_data.json file in folder: ' + curr_img_folder_path
            return msg, 'error'
    else:
        msg = 'No image folder info in file: ' + xml_file
        return msg, 'error'

    shutil.copy2(xml_file, arch_xml + Y + '/' + M + '/' + D)
    shutil.copy2(xml_file, buffer_path)
    bad_files = []
    good_files = []
    for file in df_img_paths:
        if os.path.isfile(file):
            shutil.copy2(file, buffer_path + '/' + img_folder_name)
            shutil.copy2(file, arch_img + Y + '/' + M + '/' + D + '/' + img_folder_name)
            good_files.append(file)
        else:
            bad_files.append(file)

    if len(bad_files) > 0:
        msg = 'No defects files: ' + ', '.join(bad_files)
        return msg, 'warning'
    else:
        msg = ' copied: ' + ', '.join(good_files)
        return msg, 'OK'


def get_X_y(xml_file: str, buffer_path: str):
    img_folder_name = get_dataFolderName(xml_file)

    if img_folder_name is not None:
        curr_img_folder_path = buffer_path + img_folder_name + '/'
        list_df = []

        if os.path.isfile(curr_img_folder_path + 'json_data.json'):
            df_defects_tmp = get_df_defects(xml_file, False)
            df_img_tmp = get_img_df(curr_img_folder_path)
            df_total = df_defects_tmp.merge(df_img_tmp, on='designator', how='inner')
            list_df.append(df_total)

            df_total_pre = pd.concat(list_df)
            df_total_pre = df_total_pre[df_total_pre.defect_image != 'noImage']
            df_total_pre.loc[df_total_pre.repairStatus == 'False Call', 'repairStatus'] = 1
            df_total_pre.loc[df_total_pre.repairStatus == 'Repaired', 'repairStatus'] = 0

            X = df_total_pre['img_path'].tolist()
            y = df_total_pre['repairStatus'].tolist()

        else:
            msg = 'No json_data.json file in folder: ' + curr_img_folder_path
            return msg, 'error', [], []
    else:
        msg = 'No image folder info in file: ' + xml_file
        return msg, 'error', [], []

    return '', 'OK', X, y
