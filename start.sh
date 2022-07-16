# $1 => Core tag version
# $2 => Service tag version
# $3 => Service port (default 5000)

# Example:  sh start.sh v1.0.4 v1.0.1 5000

[ -z "${MONGO_INITDB_ROOT_USERNAME}" ] && mongo_username='root' || mongo_username="${MONGO_INITDB_ROOT_USERNAME}"

[ -z "${MONGO_INITDB_ROOT_PASSWORD}" ] && mongo_password='example' || mongo_password="${MONGO_INITDB_ROOT_PASSWORD}"

[ -z "${MONGO_INITDB_DATABASE}" ] && mongo_db='measuresoftgram' || mongo_db="${MONGO_INITDB_DATABASE}"

[ -z "$1" ] && core_tag='latest' || core_tag="$1"

[ -z "$2" ] && service_tag='latest' || service_tag="$2"

[ -z "$3" ] && service_port='5000' || service_port="$3"


docker network create measuresoftgram || true

docker run --name measuresoftgram-core --network measuresoftgram --rm -d "measuresoftgram/core:${core_tag}"

docker run --name measuresoftgram-service --network measuresoftgram -p "127.0.0.1:${service_port}:5000/tcp" --env CORE_URL="http://measuresoftgram-core:5000" --rm -d "measuresoftgram/service:${service_tag}"

docker run --name measuresoftgram-db -d --network measuresoftgram --volume /db_data --rm --env MONGO_INITDB_ROOT_USERNAME="${mongo_username}" --env MONGO_INITDB_ROOT_PASSWORD="${mongo_password}" --env MONGO_INITDB_DATABASE="${mongo_db}" mongo:latest


echo "\nMeasureSoftGram Core container running successfully"
echo "MeasureSoftGram Database container running successfully"
echo "MeasureSoftGram Service ${service_tag} running in 127.0.0.1:${service_port}"
