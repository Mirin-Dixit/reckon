FROM nginx:stable-alpine@sha256:0e52bd054126cdc040b1276c0af347aeb02a41b9cfe305d6094767ac30e97949
RUN addgroup -g 10001 ragbench && adduser -D -H -u 10001 -G ragbench ragbench
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/ingress.conf /etc/nginx/ingress.conf
USER 10001:10001
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/api/v1/health
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
