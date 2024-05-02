# Serverless Functions API Documentation

Welcome to the Serverless Functions API documentation. This API enables CRUD operations on user data stored in a PostgreSQL database.

## Prerequisites
1. **Cloud Account**: Create a free tier account on your preferred cloud provider. We recommend AWS with Lambda and RDS (PostgreSQL) services.
2. **Access Setup**: Ensure access to serverless functions and set up a PostgreSQL database.
3. **AWS Layers**: Follow the instructions in the [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html) to create and attach layers, allowing you to efficiently share code and resources across multiple Lambda functions.

## Endpoints
### Create User: POST - /create_user

**Request Body:**
```json
{
  "full_name": "Peter Parker",
  "mob_num": "9876543210",
  "pan_num": "AABCP1234C"
}
```
**Response (Success):**
```json
{
  "statusCode": 200,
  "body": "User created successfully"
}
```
**Response (Error):**
```json
{
  "statusCode": 400,
  "body": "Invalid PAN card format"
}
```

### Get Users: GET - /get_users

**Response (Success - Users Found):**
```json
{
  "statusCode": 200,
  "body": {
    "users": [
      {
        "user_id": "12345",
        "full_name": "Peter Parker",
        "mob_num": "9876543210",
        "pan_num": "AABCP1234C"
      }
    ]
  }
}
```
**Response (Success - No Users Found):**
```json
{
  "statusCode": 200,
  "body": {
    "users": []
  }
}
```

### Delete User: DELETE - /delete_user

**Request Body:**
```json
{
  "user_id": "12345"
}
```
**Response (Success):**
```json
{
  "statusCode": 200,
  "body": "User deleted successfully"
}
```
**Response (Error):**
```json
{
  "statusCode": 404,
  "body": "User not found"
}
```

### Update User: PUT - /update_user

**Request Body:**
```json
{
  "user_id": "12345",
  "update_data": {
    "full_name": "Updated Name",
    "mob_num": "9876543211"
  }
}
```
**Response (Success):**
```json
{
  "statusCode": 200,
  "body": "User updated successfully"
}
```
**Response (Error):**
```json
{
  "statusCode": 400,
  "body": "Invalid mobile number format"
}
```

Feel free to use these endpoints to interact with the Serverless Functions API. Refer to the error messages in the responses for troubleshooting. Happy coding!

--- 

