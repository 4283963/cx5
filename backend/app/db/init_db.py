from app.db.database import SessionLocal
from app.models.models import Package, ConveyorBelt


def init_database():
    db = SessionLocal()
    try:
        if db.query(Package).count() == 0:
            packages = [
                Package(
                    tracking_number="SF1234567890123",
                    destination_city="北京市",
                    status="正常",
                    sender="张三",
                    receiver="李四",
                    weight=2500
                ),
                Package(
                    tracking_number="YT9876543210987",
                    destination_city="上海市",
                    status="客户拦截",
                    sender="王五",
                    receiver="赵六",
                    weight=1200
                ),
                Package(
                    tracking_number="ZTO5678901234567",
                    destination_city="广州市",
                    status="疑似违禁品",
                    sender="钱七",
                    receiver="孙八",
                    weight=800
                ),
                Package(
                    tracking_number="JD1122334455667",
                    destination_city="深圳市",
                    status="正常",
                    sender="周九",
                    receiver="吴十",
                    weight=3500
                ),
                Package(
                    tracking_number="EMS9988776655443",
                    destination_city="成都市",
                    status="客户拦截",
                    sender="郑十一",
                    receiver="王十二",
                    weight=5000
                ),
                Package(
                    tracking_number="STO2233445566778",
                    destination_city="杭州市",
                    status="正常",
                    sender="冯十三",
                    receiver="陈十四",
                    weight=1500
                ),
                Package(
                    tracking_number="YD5566778899001",
                    destination_city="武汉市",
                    status="疑似违禁品",
                    sender="褚十五",
                    receiver="卫十六",
                    weight=200
                ),
            ]
            db.add_all(packages)

        if db.query(ConveyorBelt).count() == 0:
            conveyors = [
                ConveyorBelt(
                    belt_id="CONV-001",
                    name="一号传送带",
                    status="运行中",
                    speed=60,
                    camera_id="CAM-001",
                    valve_id="VALVE-001"
                ),
                ConveyorBelt(
                    belt_id="CONV-002",
                    name="二号传送带",
                    status="运行中",
                    speed=55,
                    camera_id="CAM-002",
                    valve_id="VALVE-002"
                ),
            ]
            db.add_all(conveyors)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"初始化数据库时出错: {e}")
    finally:
        db.close()
