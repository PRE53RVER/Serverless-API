import os
import re
import uuid
import json
import psycopg2
from datetime import datetime
from http import HTTPStatus
from config import config

def create_connection():
    """Create a database connection and return it."""
    params = config()
    try:
        conn = psycopg2.connect(**params)
        return conn
    except (Exception, psycopg2.Error) as error:
        print(f'Error: {error}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "Failed to connect to the database."
            })
        }

def is_valid_mobile_number(mob_num):
    """Validate the mobile number."""
    if len(mob_num) == 10 and mob_num.isdigit():
        return True
    return False

def is_valid_pan_number(pan_num):
    """Validate the PAN number."""
    pattern = r'^[A-Z]{5}\d{4}[A-Z]$'
    return bool(re.fullmatch(pattern, pan_num))

def is_valid_manager_id(manager_id, conn, cur):
    """Validate the manager ID."""
    query = "SELECT COUNT(*) FROM managers WHERE manager_id = %s"
    cur.execute(query, (manager_id,))
    count = cur.fetchone()[0]
    return count > 0

def handle_manager_update(user_id, new_manager_id, cur, conn):
    """Update the manager ID and handle related operations."""
    query = "SELECT manager_id FROM users WHERE user_id = %s AND is_active = true"
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    current_manager_id = result[0] if result else None

    if current_manager_id is None:
        query = "UPDATE users SET manager_id = %s, updated_at = %s WHERE user_id = %s"
        cur.execute(query, (new_manager_id, datetime.now(), user_id))
    else:
        query = "UPDATE users SET is_active = false WHERE user_id = %s AND manager_id = %s"
        cur.execute(query, (user_id, current_manager_id))
        new_user_id = str(uuid.uuid4())[:36]
        query = "INSERT INTO users (user_id, full_name, mob_num, pan_num, manager_id, created_at, updated_at, is_active) SELECT %s, full_name, mob_num, pan_num, %s, created_at, %s, true FROM users WHERE user_id = %s AND is_active = false"
        cur.execute(query, (new_user_id, new_manager_id, datetime.now(), user_id))

    conn.commit()

def create_user(event, context):
    """Create a new user."""
    try:
        body = event.get('body')
        if not body:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Request body is missing."
                })
            }

        data = json.loads(body)

        full_name = data.get('full_name', '').strip()
        if not full_name:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Full name is required."
                })
            }

        mob_num = data.get('mob_num', '').strip()
        mob_num = re.sub(r'^0|^\+91', '', mob_num)
        if not is_valid_mobile_number(mob_num):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Invalid mobile number."
                })
            }

        pan_num = data.get('pan_num', '').strip().upper()
        if not is_valid_pan_number(pan_num):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Invalid PAN number."
                })
            }

        manager_id = data.get('manager_id')
        conn = create_connection()
        if isinstance(conn, dict):
            return conn

        cur = conn.cursor()
        if manager_id and not is_valid_manager_id(manager_id, conn, cur):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Invalid manager ID."
                })
            }

        user_id = str(uuid.uuid4())[:36]
        created_at = datetime.now()
        query = "INSERT INTO users (user_id, full_name, mob_num, pan_num, manager_id, created_at, updated_at, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (user_id, full_name, mob_num, pan_num, manager_id, created_at, None, True)
        cur.execute(query, values)
        conn.commit()

        cur.close()
        conn.close()

        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({
                "status": "Success",
                "message": f'User created successfully with ID: {user_id}'
            })
        }

    except (Exception, psycopg2.Error) as error:
        print(f'Error: {error}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while creating the user."
            })
        }

def get_users(event, context):
    """Retrieve users based on filter criteria."""
    try:
        conn = create_connection()
        if isinstance(conn, dict):
            return conn

        cur = conn.cursor()

        query_params = []
        query = "SELECT user_id, manager_id, full_name, mob_num, pan_num, created_at, updated_at, is_active FROM users"

        if event.get('body'):
            data = json.loads(event.get('body'))
            if 'user_id' in data:
                query += " WHERE user_id = %s"
                query_params.append(data['user_id'])
            elif 'mob_num' in data:
                query += " WHERE mob_num = %s"
                query_params.append(data['mob_num'])
            elif 'manager_id' in data:
                query += " WHERE manager_id = %s"
                query_params.append(data['manager_id'])

        cur.execute(query, tuple(query_params))
        users = cur.fetchall()

        cur.close()
        conn.close()

        if not users:
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({"users": []})
            }

        formatted_users = []
        for user in users:
            formatted_user = {
                'user_id': user[0],
                'manager_id': user[1],
                'full_name': user[2],'mob_num': user[3],
                'pan_num': user[4],
                'created_at': user[5].isoformat(),
                'updated_at': user[6].isoformat() if user[6] else None,
                'is_active': user[7]
            }
            formatted_users.append(formatted_user)

        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({"users": formatted_users})
        }

    except (Exception, psycopg2.Error) as error:
        print(f'Error: {error}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while retrieving users."
            })
        }

def delete_user(event, context):
    """Delete a user based on user_id or mob_num."""
    try:
        conn = create_connection()
        if isinstance(conn, dict):
            return conn

        cur = conn.cursor()

        body = json.loads(event.get('body'))
        user_id = body.get('user_id')
        mob_num = body.get('mob_num')

        if not user_id and not mob_num:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Either user_id or mob_num is required."
                })
            }

        query = "DELETE FROM users WHERE "
        if user_id:
            query += "user_id = %s"
            cur.execute(query, (user_id,))
        else:
            query += "mob_num = %s"
            cur.execute(query, (mob_num,))

        conn.commit()
        cur.close()
        conn.close()

        if cur.rowcount == 0:
            return {
                'statusCode': HTTPStatus.NOT_FOUND,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "User not found."
                })
            }

        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({"status": "Success", "message": "User deleted successfully."})
        }

    except (Exception, psycopg2.Error) as error:
        print(f'Error: {error}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while deleting the user."
            })
        }

def update_user(event, context):
    """Update users based on user_ids and update_data."""
    try:
        conn = create_connection()
        if isinstance(conn, dict):
            return conn

        cur = conn.cursor()

        body = json.loads(event.get('body'))
        user_ids = body.get('user_ids')
        update_data = body.get('update_data')

        if not user_ids or not update_data:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Both user_ids and update_data are required."
                })
            }

        if len(user_ids) != len(update_data):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "The number of user_ids and update_data items should be the same."
                })
            }

        query = "SELECT user_id FROM users WHERE user_id = %s"
        existing_user_ids = []
        non_existing_user_ids = []
        for user_id in user_ids:
            cur.execute(query, (user_id,))
            if cur.fetchone():
                existing_user_ids.append(user_id)
            else:
                non_existing_user_ids.append(user_id)

        skipped_user_ids = []
        for user_id in existing_user_ids:
            user_update_data = update_data.get(user_id)

            if not user_update_data:
                continue

            full_name = user_update_data.get('full_name', '').strip()
            mob_num = user_update_data.get('mob_num', '').strip()
            mob_num = re.sub(r'^0|^\+91', '', mob_num)
            pan_num = user_update_data.get('pan_num', '').strip().upper()
            manager_id = user_update_data.get('manager_id')

            if full_name and not full_name:
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Full name cannot be empty."
                    })
                }

            if mob_num and not is_valid_mobile_number(mob_num):
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Invalid mobile number."
                    })
                }

            if pan_num and not is_valid_pan_number(pan_num):
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Invalid PAN number."
                    })
                }

            if manager_id and not is_valid_manager_id(manager_id, conn, cur):
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Invalid manager ID."
                    })
                }

            update_keys = []
            update_values = []
            if 'full_name' in user_update_data:
                update_keys.append('full_name')
                update_values.append(full_name)
            if 'mob_num' in user_update_data:
                update_keys.append('mob_num')
                update_values.append(mob_num)
            if 'pan_num' in user_update_data:
                update_keys.append('pan_num')
                update_values.append(pan_num)
            if 'manager_id' in user_update_data:
                handle_manager_update(user_id, manager_id, cur, conn)
            else:
                update_keys.append('updated_at')
                update_values.append(datetime.now())

            set_clause = ', '.join([f"{key} = %s" for key in update_keys])
            query = f"UPDATE users SET {set_clause} WHERE user_id = %s"
            values = update_values + [user_id]
            cur.execute(query, values)

        if non_existing_user_ids:
            skipped_user_ids = non_existing_user_ids

        conn.commit()
        cur.close()
        conn.close()

        if skipped_user_ids:
            skipped_users_message = ', '.join(skipped_user_ids)
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({
                    "status": "Partial Success",
                    "message": "Users updated successfully.",
                    "skipped_users": skipped_users_message
                })
            }
        else:
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({
                    "status": "Success",
                    "message": "Users updated successfully."
                })
            }

    except (Exception, psycopg2.Error) as error:
        print(f'Error: {error}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while updating users."
            })
        }