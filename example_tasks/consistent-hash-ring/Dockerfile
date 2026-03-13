FROM gdm-base:latest

WORKDIR /app
# Copy skills
COPY skills /root/.claude/skills

# Copy input files
COPY input_files/ /app/

# Copy and run setup script
COPY setup.sh /tmp/
RUN chmod +x /tmp/setup.sh && /tmp/setup.sh
