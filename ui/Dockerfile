# set the base image
# n/b: for production, node is only used for building 
# the static Html and javascript files
# as react creates static html and js files after build
# these are what will be served by nginx
# use alias build to be easier to refer this container elsewhere
# e.g inside nginx container
FROM node:slim AS build
# set working directory
# this is the working folder in the container
# from which the app will be running from
WORKDIR /ui
# copy everything to /ui directory
# as opposed to on dev, in prod everything is copied to docker
COPY ./package*.json /ui
# add the node_modules folder to $PATH
# ENV PATH /ui/node_modules/.bin:$PATH
# install and cache dependencies
RUN npm install
#build the project for production

COPY ./ /ui
RUN npm run build

# set up production environment
# the base image for this is an alpine based nginx image
FROM nginx:alpine
# copy the build folder from react to the root of nginx (www)
COPY --from=build /ui/dist /var/www
# --------- only for those using react router ----------
# if you are using react router 
# you need to overwrite the default nginx configurations
# remove default nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf
# replace with custom one
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
# --------- /only for those using react router ----------
# expose port 80 to the outer world
EXPOSE 80 443
# start nginx 
CMD ["nginx", "-g", "daemon off;"]
