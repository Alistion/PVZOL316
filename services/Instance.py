# services/Instance.py

class InstanceService:
    @staticmethod
    def display(username):
        """
        获取副本(狩猎场/内世界)的关卡拓扑图
        对应接口: api.fuben.display
        """
        # 严格按照抓包提取的 31 个关卡节点数据，注意区分 String 和 Number
        caves_data = [
            {"reward": "123", "parent": "", "min_grade": "101", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "1", "vid": "1", "money": "0", "t": "0", "name": "副本2.1-01", "open_tools": "25|50", "child": "2,14", "status": 5},
            {"reward": "123", "parent": "", "min_grade": "102", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "2", "vid": "2", "money": "0", "t": "0", "name": "副本2.1-02", "open_tools": "123|50", "child": "3", "status": 5},
            {"reward": "124", "parent": "", "min_grade": "103", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "3", "vid": "3", "money": "0", "t": "0", "name": "副本2.1-03", "open_tools": "123|50", "child": "4", "status": 5},
            {"reward": "124", "parent": "", "min_grade": "104", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "4", "vid": "4", "money": "0", "t": "0", "name": "副本2.1-04", "open_tools": "124|50", "child": "5,18", "status": 5},
            {"reward": "670", "parent": "", "min_grade": "105", "open_cave_grid": "10", "lcc": 1010, "point": "5", "cave_id": "5", "vid": "5", "money": "0", "t": "0", "name": "副本2.1-05", "open_tools": "124|50", "child": "", "status": 5},
            {"reward": "125", "parent": "", "min_grade": "106", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "14", "vid": "6", "money": "0", "t": "0", "name": "副本2.1-06", "open_tools": "125|50,670|50", "child": "13", "status": 5},
            {"reward": "126", "parent": "", "min_grade": "107", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "13", "vid": "7", "money": "0", "t": "0", "name": "副本2.1-07", "open_tools": "125|50", "child": "12", "status": 5},
            {"reward": "126", "parent": "", "min_grade": "108", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "12", "vid": "8", "money": "0", "t": "0", "name": "副本2.1-08", "open_tools": "126|50", "child": "11", "status": 5},
            {"reward": "127", "parent": "", "min_grade": "109", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "11", "vid": "9", "money": "0", "t": "0", "name": "副本2.1-09", "open_tools": "126|50", "child": "10", "status": 5},
            {"reward": "127", "parent": "", "min_grade": "110", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "10", "vid": "10", "money": "0", "t": "0", "name": "副本2.1-10", "open_tools": "127|50", "child": "15", "status": 5},
            {"reward": "128", "parent": "", "min_grade": "111", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "15", "vid": "11", "money": "0", "t": "0", "name": "副本2.1-11", "open_tools": "127|50", "child": "16", "status": 5},
            {"reward": "128", "parent": "", "min_grade": "112", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "16", "vid": "12", "money": "0", "t": "0", "name": "副本2.1-12", "open_tools": "128|50", "child": "17", "status": 5},
            {"reward": "634", "parent": "", "min_grade": "113", "open_cave_grid": "10", "lcc": 10, "point": "5", "cave_id": "17", "vid": "13", "money": "0", "t": "0", "name": "副本2.1-13", "open_tools": "128|50", "child": "22", "status": 5},
            {"reward": "129", "parent": "", "min_grade": "114", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "18", "vid": "14", "money": "0", "t": "0", "name": "副本2.1-14", "open_tools": "129|50,634|50", "child": "19", "status": 5},
            {"reward": "130", "parent": "", "min_grade": "115", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "19", "vid": "15", "money": "0", "t": "0", "name": "副本2.1-15", "open_tools": "129|50", "child": "20", "status": 5},
            {"reward": "130", "parent": "", "min_grade": "116", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "20", "vid": "16", "money": "0", "t": "0", "name": "副本2.1-16", "open_tools": "130|50", "child": "23", "status": 5},
            {"reward": "131", "parent": "", "min_grade": "117", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "22", "vid": "17", "money": "0", "t": "0", "name": "副本2.1-17", "open_tools": "130|50", "child": "21", "status": 5},
            {"reward": "131", "parent": "", "min_grade": "118", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "21", "vid": "18", "money": "0", "t": "0", "name": "副本2.1-18", "open_tools": "131|50", "child": "6", "status": 5},
            {"reward": "132", "parent": "", "min_grade": "119", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "6", "vid": "19", "money": "0", "t": "0", "name": "副本2.1-19", "open_tools": "131|50", "child": "7", "status": 5},
            {"reward": "132", "parent": "", "min_grade": "120", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "7", "vid": "20", "money": "0", "t": "0", "name": "副本2.1-20", "open_tools": "132|50", "child": "8", "status": 5},
            {"reward": "133", "parent": "", "min_grade": "121", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "8", "vid": "21", "money": "0", "t": "0", "name": "副本2.1-21", "open_tools": "132|50", "child": "9,28", "status": 5},
            {"reward": "133", "parent": "", "min_grade": "122", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "28", "vid": "22", "money": "0", "t": "0", "name": "副本2.1-22", "open_tools": "133|50", "child": "29", "status": 5},
            {"reward": "134", "parent": "", "min_grade": "123", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "29", "vid": "23", "money": "0", "t": "0", "name": "副本2.1-23", "open_tools": "133|50", "child": "30", "status": 5},
            {"reward": "134", "parent": "", "min_grade": "124", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "30", "vid": "24", "money": "0", "t": "0", "name": "副本2.1-24", "open_tools": "134|50", "child": "31", "status": 5},
            {"reward": "675", "parent": "", "min_grade": "125", "open_cave_grid": "10", "lcc": 10, "point": "5", "cave_id": "31", "vid": "25", "money": "0", "t": "0", "name": "副本2.1-25", "open_tools": "134|50", "child": "", "status": 5},
            {"reward": "135", "parent": "", "min_grade": "126", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "23", "vid": "26", "money": "0", "t": "0", "name": "副本2.1-26", "open_tools": "135|50,675|50", "child": "24", "status": 5},
            {"reward": "136", "parent": "", "min_grade": "127", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "24", "vid": "27", "money": "0", "t": "0", "name": "副本2.1-27", "open_tools": "135|50", "child": "25", "status": 5},
            {"reward": "136", "parent": "", "min_grade": "128", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "25", "vid": "28", "money": "0", "t": "0", "name": "副本2.1-28", "open_tools": "136|50", "child": "26", "status": 5},
            {"reward": "137", "parent": "", "min_grade": "129", "open_cave_grid": "10", "lcc": -1, "point": "5", "cave_id": "26", "vid": "29", "money": "0", "t": "0", "name": "副本2.1-29", "open_tools": "136|50", "child": "27", "status": 5},
            {"reward": "640", "parent": "", "min_grade": "130", "open_cave_grid": "10", "lcc": 10, "point": "5", "cave_id": "27", "vid": "30", "money": "0", "t": "0", "name": "副本2.1-30", "open_tools": "137|50", "child": "", "status": 5},
            {"reward": "644", "parent": "", "min_grade": "131", "open_cave_grid": "10", "lcc": 10, "point": "5", "cave_id": "9", "vid": "31", "money": "0", "t": "0", "name": "副本2.1-31", "open_tools": "137|50,640|50", "child": "", "status": 5}
        ]

        # 拼装返回给 Flash 的完整面板数据
        return {
            "_reward": 0,
            "_lcc": 160,
            "_last_challenge_cave": None,
            "_open_scenes": ["1", "2", "3", "4", "5"],
            "_caves": caves_data,
            "_integral": 155
        }