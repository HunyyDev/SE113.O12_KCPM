from app import driver, logger


def match_person_nodes(tx, uid1: str, uid2: str):
    tx.run('MERGE (p1:Person {uid: "' + uid1 + '"})')
    tx.run('MERGE (p2:Person {uid: "' + uid2 + '"})')
    tx.run(
        'MATCH (p1:Person {uid: "'
        + uid1
        + '"}) MATCH (p2:Person {uid: "'
        + uid2
        + '"}) MERGE (p1)-[:FRIEND]-(p2)'
    )


async def insert2PersonAndSetFriend(uid1: str, uid2: str):
    logger.info(uid1 + " " + uid2)
    with driver.session() as session:
        session.write_transaction(match_person_nodes, uid1, uid2)


async def deleteFriend(uid1: str, uid2: str):
    await driver.execute_query(
        'MATCH (p1:Person {uid: "'
        + uid1
        + '"})-[r:FRIEND]-(p2:Person {uid: "'
        + uid2
        + '"}) DELETE r'
    )
