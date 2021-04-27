#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <pthread.h>
#include <unistd.h>
#include <math.h>
#include <string.h>
#include <signal.h>

#include <time.h>
#include <sys/time.h>

#include "crespin.h"
#include "communication.h"


#define DEBUG 0

#if DEBUG == 0
  #include <wiringPi.h>
#endif

/*********** STATUS ************/

#define STATUS_PAUSE 0
#define STATUS_RUN 1
#define STATUS_SHUTDOWN 2
#define STATUS_TO_TARGET 3
char STATUS_NAMES [4][9] = {"pause", "run", "shutdown", "totarget"};

int status = STATUS_PAUSE;
int emergency_stop = 0; // used to detect double CTRL+C catch

/*********** MOTORS ************/

#define NB_MOTS 22

uint32_t motors_positions [NB_MOTS]; // increasing position = going down
uint32_t motors_targets [NB_MOTS];
uint8_t motors_seq_state [NB_MOTS]; // 0..7
uint8_t motors_seq_state_prev [NB_MOTS] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}; // 0..7
int8_t motors_reverse [NB_MOTS] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}; // +1 / -1

int motors_moved = 0;

#define MOTOR_SEQ_N 8
#define MOTOR_SEQ_NB_BITS 4
uint8_t MOTOR_SEQ [8][4] = {{1, 0, 0, 0}, // 8
                            {1, 1, 0, 0}, // 12
                            {0, 1, 0, 0}, // 4
                            {0, 1, 1, 0}, // 6
                            {0, 0, 1, 0}, // 2
                            {0, 0, 1, 1}, // 3
                            {0, 0, 0, 1}, // 1
                            {1, 0, 0, 1}}; // 9. going forward in the seq if go forward in the position = going down

/*********** SEQUENCE ************/

#define SEQ_MOT_SPACING 0.45
#define SEQ_MOT_STEP (1.0 / 3800) // ensures a max variation of 1 motor step
#define SEQ_AMPLITUDE 3800
#define SEQ_BIAS 19000
#define SEQ_STEP_MODULO 23876 // step * SEQ_MOT_STEP = 2pi <=> 2 pi / SEQ_MOT_STEP
uint32_t step = 0;

uint64_t last_step_time_us = 0; // requires uint64_t on 32 bits ARM
uint64_t step_time_ms = 3000; // // < 4000 μs  // 1/2s = 500000

/*********** PINS ************/

#define PIN_DATA 17
#define PIN_CLOCK 22
#define PIN_OUT 27



/****************************************/
/*********** TOOLS FUNCTIONS ************/
/****************************************/

/**
 * Return timestamp in microseconds
 */
uint64_t get_time() {
    struct timeval curTime;
    gettimeofday(&curTime, NULL);
    return (uint64_t)curTime.tv_sec * 1000000 + curTime.tv_usec;
}

/**
 * Wait for a small delay in micro-second, must be less than 1s
 */
void small_delay_us (unsigned int delay) // less than 1s !
{
    struct timespec sleeper;

    sleeper.tv_sec  = 0;
    sleeper.tv_nsec = delay * 1000L;
    nanosleep (&sleeper, NULL);
}

/*
 * Get next int to read from a string, starting at start. Outputed in number,
 * output is the end position of the number+1 or -1 if none found
 */
int get_next_uint(char string[], int start, uint32_t* number) {
    if (start < 0) start = 0;
    int i, found = 0;
    *number = 0;
    for (i = start; i < strlen(string); i++) {
        if (string[i] >= '0' && string[i] <= '9') {
            found = 1;
            *number = *number * 10 + string[i] - '0';
        }
        else if (found)
            break;
    }

    return found ? i : -1;
}


/*****************************************/
/*********** MOTORS MOVEMENTS ************/
/*****************************************/

void print_motors() {
    printf("--------------------------------------------------------------------------------\nid  ");
                      for (int i = 0; i < NB_MOTS/2; i++) printf("%6d ", i);
    printf("\npos "); for (int i = 0; i < NB_MOTS/2; i++) printf("%6d ", motors_positions[i]);
    printf("\ntar "); for (int i = 0; i < NB_MOTS/2; i++) printf("%6d ", motors_targets[i]);
    printf("\nseq "); for (int i = 0; i < NB_MOTS/2; i++) printf("%6d ", motors_seq_state[i]);
    printf("\n--------------------------------------------------------------------------------\nid  ");
                      for (int i = NB_MOTS/2; i < NB_MOTS; i++) printf("%6d ", i);
    printf("\npos "); for (int i = NB_MOTS/2; i < NB_MOTS; i++) printf("%6d ", motors_positions[i]);
    printf("\ntar "); for (int i = NB_MOTS/2; i < NB_MOTS; i++) printf("%6d ", motors_targets[i]);
    printf("\nseq "); for (int i = NB_MOTS/2; i < NB_MOTS; i++) printf("%6d ", motors_seq_state[i]);
    printf("\n--------------------------------------------------------------------------------\n");
}

/*
 * Compute motors targets based on current step
 */
void compute_targets() {
    for (int i = 0; i < NB_MOTS / 2; i++) {
        motors_targets[2*i] = (long) (cos(i * SEQ_MOT_SPACING + step * SEQ_MOT_STEP) * SEQ_AMPLITUDE + SEQ_BIAS);
        motors_targets[2*i + 1] = motors_targets[2*i];
    }
}

/*
 * Update motors step to bring the motor closer to the target
 */
int compute_motors_next_pos() {
    if (!motors_moved) {
        printf("Can't compute new pos. Motors haven't moved since last update\n");
    }

    motors_moved = 0;

    int direction, direction_seq, motors_need_to_move = 0;

    for (int i = 0; i < NB_MOTS; i++) {
        if (motors_positions[i] != motors_targets[i]) {
            motors_need_to_move = 1;
            // 1: increase pos / -1: decrease pos
            if (motors_positions[i] < motors_targets[i])
                direction = 1;
            else
                direction = -1;
            direction_seq = direction * motors_reverse[i]; // corrected for reverse motors
            motors_seq_state[i] = (motors_seq_state[i] + direction_seq + MOTOR_SEQ_N) % MOTOR_SEQ_N; // +MOTOR_SEQ_N to force >0 seq state
            motors_positions[i] += direction;
        }
    }

    return motors_need_to_move;
}

/*
 * Output motor position to the register
 */
void output_motors_command() {
    if (motors_moved) {
        printf("already uptodate");
        return;
    }

    motors_moved = 1;

    for (int k = 0; k < NB_MOTS; k++) {
        motors_seq_state_prev[k] = motors_seq_state[k];
        #if DEBUG == 0
        for (int i = 0; i < NB_MOTS; i++) {
            for (int j = 0; j < MOTOR_SEQ_NB_BITS; j++) {
                digitalWrite(PIN_DATA, MOTOR_SEQ[motors_seq_state_prev[i]][j]);
                digitalWrite(PIN_CLOCK, HIGH);
                digitalWrite(PIN_CLOCK, LOW);
            }
        }
        #endif


        uint64_t now_us = get_time();
        int64_t wait_delay = (int64_t) last_step_time_us + step_time_ms / NB_MOTS - (int64_t) now_us;
        //  printf("%lld us delay\n", wait_delay);

        if (wait_delay > 10) {
            small_delay_us(wait_delay);
            now_us = get_time();
        }

        #if DEBUG == 0
          digitalWrite(PIN_OUT, HIGH);
          digitalWrite(PIN_OUT, LOW);
        #endif

        last_step_time_us = now_us;
    }
}

/**
 * Do n steps
 */
void steps(int n) {
    for (int i = 0; i < n; i++) {
        compute_targets();
        compute_motors_next_pos();
        output_motors_command();
        if (step == SEQ_STEP_MODULO - 1) {
            printf("Before modulo\n");
            print_motors();
        }
        if (step == 0) {
            printf("After modulo\n");
            print_motors();
        }
        step = (step + 1) % SEQ_STEP_MODULO;
    }
}

/**
 * Move motors so that they reach the target
 */
void move_motors_to_target() {
    while (compute_motors_next_pos() && status == STATUS_TO_TARGET) { // compute_motors_next_pos indicates if motors need to be moved
        output_motors_command();
    }
    output_motors_command();
}


/**
 * Load and save positions of the motors
 */
void load_positions() {
    FILE* fp = fopen("motors.bin", "rb");
    if(fp == NULL) return;
    size_t s = sizeof(motors_positions[0]);
    fread(motors_positions, s, sizeof(motors_positions) / s, fp);
    fclose(fp);
}

void save_positions() {
    FILE* fp = fopen("motors.bin", "wb");
    if(fp == NULL) return;
    size_t s = sizeof(motors_positions[0]);
    fwrite(motors_positions, s, sizeof(motors_positions) / s, fp);
    fclose(fp);
}


void *motors(void *arg) {
    #if DEBUG == 0
      wiringPiSetupGpio();

      pinMode(PIN_DATA, OUTPUT);
      pinMode(PIN_CLOCK, OUTPUT);
      pinMode(PIN_OUT, OUTPUT);
    #endif

    // init targets & motors, load motors previous positions
    printf("motors control started, load previous position\n");
    load_positions();
    compute_targets();
    output_motors_command();
    print_motors();

    // looping until shutdown
    while (status != STATUS_SHUTDOWN) {
        if (status == STATUS_RUN) {
            steps(100);
            printf("motors running, global step %d\n", step);
        }
        else if (status == STATUS_TO_TARGET) {
            move_motors_to_target();
            sleep (1);
        }
        else {
            sleep(1);
            #if DEBUG
              printf("motors paused...\n");
            #endif
        }
    }

    // save final motor positions before shutdown
    printf("motors control stopping, saving position\n");
    save_positions();
    printf("... position saved\n");

    pthread_exit(NULL);
}




void server_process_request(char data[], char reply[]) {
    if (strncmp(data, "pause", 5) == 0) {
        status = STATUS_PAUSE;
        strcpy(reply, "OK pause");
    }

    else if (strncmp(data, "run", 3) == 0) {
        status = STATUS_RUN;
        strcpy(reply, "OK run");
    }

    else if (strncmp(data, "setspeed", 8) == 0) {
        uint32_t val;
        if (get_next_uint(data, 0, &val) < 0) {
            strcpy(reply, "ERR setdata : did not found speed");
            return;
        }
        if (val < 1000)
            val = 1000;
        step_time_ms = val;
        strcpy(reply, "OK run");
    }

    else if (strncmp(data, "shutdown", 8) == 0) {
        status = STATUS_SHUTDOWN;
        strcpy(reply, "OK shutdown");
    }

    else if (strncmp(data, "totarget", 8) == 0) {
        status = STATUS_TO_TARGET;
        strcpy(reply, "OK move to target");
    }

    else if (strncmp(data, "data", 4) == 0) {
        print_motors();
        reply[0] = '\0';
        reply += sprintf(reply, "%s\n", STATUS_NAMES[status]);
        reply += sprintf(reply, "%llu\n", step_time_ms);
        for (int i = 0; i < NB_MOTS; i++)
            reply += sprintf(reply, "%d,%d\n", motors_positions[i], motors_targets[i]);
            // increment reply by the number of written chars
    }

    else if (strncmp(data, "settarget", 9) == 0) {
        uint32_t motors_targets_tmp [NB_MOTS];
        int pos = 0;
        uint32_t val;

        for (int i = 0; i < NB_MOTS; i++) {
            pos = get_next_uint(data, pos, &val);
            if (pos < 0) {
                strcpy(reply, "ERR setdata : did not found enough ints");
                return;
            }
            motors_targets_tmp[i] = val;
        }

        memcpy(motors_targets, motors_targets_tmp, sizeof(motors_targets));

        strcpy(reply, "OK updated targets");
    }

    else if (strncmp(data, "setdata", 7) == 0) {
        uint32_t motors_positions_tmp [NB_MOTS];
        uint32_t motors_targets_tmp [NB_MOTS];
        int pos = 0;
        uint32_t val;

        for (int i = 0; i < 2*NB_MOTS; i++) {
            pos = get_next_uint(data, pos, &val);
            if (pos < 0) {
                strcpy(reply, "ERR setdata : did not found enough ints");
                return;
            }
            if (i % 2 == 0)
                motors_positions_tmp[i / 2] = val;
            else
                motors_targets_tmp[i / 2] = val;
        }

        memcpy(motors_positions, motors_positions_tmp, sizeof(motors_positions));
        memcpy(motors_targets, motors_targets_tmp, sizeof(motors_targets));

        strcpy(reply, "OK updadte targets & positions");
    }
    /*
    else if (strncmp(data, "target", 6) == 0 || strncmp(data, "position", 8) == 0) {
        uint32_t motor_id, val;
        int pos;
        pos = get_next_uint(data, 0, &motor_id);
        pos = get_next_uint(data, pos, &val);
        if (pos < 0) {
            strcpy(reply, "ERR target(mot_id, val) : did not found ints");
            return;
        }
        if (motor_id >= NB_MOTS) {
            strcpy(reply, "ERR target(mot_id, val) : mot_id invalid");
            return;
        }

        if (strncmp(data, "target", 6) == 0)
            motors_targets[motor_id] = val;
        else
            motors_positions[motor_id] = val;
        strcpy(reply, "OK update status");
    }*/
    else {
        strcpy(reply, "ERR no command found");
    }
}

void *server(void *arg) {
    int socket, client_socket;
    char data [512], reply [512];

    socket = start_server(1337);

    printf("Server running, listening on port 1337...\n");

    while(status != STATUS_SHUTDOWN) {
        client_socket = wait_for_client(socket);
        read_data(client_socket, data, 512);
        printf("got %s\n", data);
        server_process_request(data, reply);
        send_data(client_socket, reply);
        close(client_socket);
    }

    close(socket);

    pthread_exit(NULL);
}

void shutdown(int signal) {
    if (emergency_stop)
        exit(-1);
    emergency_stop = 1;
    status = STATUS_SHUTDOWN;
    printf("Exitting...\n");
}

int main(void) {
    signal(SIGTSTP, shutdown);
    signal(SIGINT, shutdown);

    pthread_t server_thread;
    pthread_t motors_thread;


    if (pthread_create(&server_thread, NULL, server, NULL)) {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    if (pthread_create(&motors_thread, NULL, motors, NULL)) {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    if (pthread_join(motors_thread, NULL)) {
        perror("pthread_join");
        return EXIT_FAILURE;
    }

    if (pthread_join(server_thread, NULL)) {
        perror("pthread_join");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
