<template>
  <section class="card admin-block">
    <h3>Админ-панель</h3>
    
    <!-- Вкладки -->
    <div class="tabs">
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'metrics' }"
        @click="activeTab = 'metrics'"
      >
        Метрики
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        Пользователи
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'ai' }"
        @click="activeTab = 'ai'"
      >
        Настройки ИИ
      </button>
    </div>

    <!-- Состояния загрузки и ошибок -->
    <div v-if="isLoading" class="admin-loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>
    
    <div v-else-if="error" class="admin-error">
      <p>{{ error }}</p>
      <button @click="retryLoad">Повторить</button>
    </div>

    <!-- Содержимое вкладки Метрики -->
    <div v-else-if="activeTab === 'metrics'" class="tab-content">
      <div class="admin-actions">
        <button @click="loadMetrics" class="refresh-btn">Обновить</button>
      </div>

      <!-- Секция метрик -->
      <div class="ai-section">
        <h4>Метрики</h4>
        <div v-if="metrics.length === 0" class="no-data">
          Нет метрик
        </div>
        
        <div v-else class="table-wrapper">
          <div class="metrics-table">
            <div class="table-header">
              <div class="col-id">ID</div>
              <div class="col-name">Название</div>
              <div class="col-desc">Описание</div>
              <div class="col-weight">Вес</div>
              <div class="col-actions">Действия</div>
            </div>
            
            <div v-for="metric in metrics" :key="metric.id" class="table-row">
              <div class="col-id">{{ metric.id }}</div>
              <div class="col-name">
                <input 
                  v-if="editingMetricId === metric.id" 
                  v-model="editMetricForm.name" 
                  type="text" 
                  class="edit-input"
                />
                <span v-else>{{ metric.name }}</span>
              </div>
              <div class="col-desc">
                <input 
                  v-if="editingMetricId === metric.id" 
                  v-model="editMetricForm.description" 
                  type="text" 
                  class="edit-input"
                />
                <span v-else>{{ metric.description || '-' }}</span>
              </div>
              <div class="col-weight">
                <input 
                  v-if="editingMetricId === metric.id" 
                  v-model.number="editMetricForm.weight" 
                  type="number" 
                  step="0.1" 
                  class="edit-input"
                />
                <span v-else>{{ metric.weight }}</span>
              </div>
              <div class="col-actions">
                <template v-if="editingMetricId === metric.id">
                  <button @click="saveMetric(metric.id)" class="save-btn">✓</button>
                  <button @click="cancelEditMetric" class="cancel-btn">✗</button>
                </template>
                <template v-else>
                  <button @click="startEditMetric(metric)" class="edit-btn">✎</button>
                  <button @click="deleteMetric(metric.id)" class="delete-btn" title="Удалить метрику">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 512 512">
                      <g>
                        <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                      </g>
                    </svg>
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Содержимое вкладки Пользователи -->
    <div v-else-if="activeTab === 'users'" class="tab-content">
      <div class="admin-actions">
        <button @click="loadUsers" class="refresh-btn">Обновить</button>
      </div>

      <!-- Форма создания воркера -->
      <div class="create-worker-form">
        <h4>Создать воркера</h4>
        <div class="form-row">
          <input v-model="newWorkerForm.email" type="email" placeholder="Email" class="form-input" />
          <input v-model="newWorkerForm.password" type="password" placeholder="Пароль" class="form-input" />
          <input v-model="newWorkerForm.name" type="text" placeholder="Имя" class="form-input" />
          <button @click="createWorker" class="add-btn">Создать</button>
        </div>
      </div>

      <!-- Поиск пользователей -->
      <div class="search-users">
        <h4>Поиск пользователей</h4>
        <div class="search-row">
          <input 
            v-model="searchQuery" 
            @keyup.enter="searchUsers" 
            type="text" 
            placeholder="Введите email для поиска"
            class="search-input"
          />
          <button @click="searchUsers" class="search-btn">Найти</button>
        </div>
      </div>

      <!-- Статистика выбранного пользователя -->
      <div v-if="selectedUserStats" class="user-stats-card">
        <h4>Статистика: {{ selectedUserName }}</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Анализов сегодня:</span>
            <span class="stat-value">{{ selectedUserStats.analysis }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Чатов сегодня:</span>
            <span class="stat-value">{{ selectedUserStats.chat }}</span>
          </div>
        </div>
        <button @click="selectedUserStats = null" class="close-stats-btn">Закрыть</button>
      </div>

      <!-- Управление рангами пользователя -->
      <div v-if="selectedUserRanks !== null" class="user-ranks-card">
        <h4>Управление рангами: {{ selectedUserName }}</h4>
        <div class="ranks-current">
          <h5>Текущие ранги:</h5>
          <div v-if="selectedUserRanks.length === 0" class="no-ranks">Нет активных рангов</div>
          <div v-else class="ranks-list">
            <div v-for="rank in selectedUserRanks" :key="rank.rank" class="rank-item">
              <span class="rank-name">{{ rank.rank }}</span>
              <span v-if="rank.expires_at" class="rank-expires">до {{ formatDate(rank.expires_at) }}</span>
              <button 
                @click="removeRank(rank.rank)" 
                class="remove-rank-btn"
                :disabled="rank.rank === 'admin'"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
        <div class="add-rank-form">
          <h5>Добавить ранг:</h5>
          <div class="form-row">
            <select v-model="newRankName" class="form-select">
              <option value="">Выберите ранг</option>
              <option v-for="rank in allRanks" :key="rank.id" :value="rank.name">
                {{ rank.name }} (уровень {{ rank.level }})
              </option>
            </select>
            <button @click="assignRank" class="add-rank-btn" :disabled="!newRankName">Назначить</button>
          </div>
        </div>
        <button @click="selectedUserRanks = null" class="close-ranks-btn">Закрыть</button>
      </div>

      <div v-if="users.length === 0" class="no-data">
        Нет пользователей
      </div>
      
      <div v-else class="table-wrapper">
        <div class="users-table">
          <div class="table-header">
            <div class="col-id">ID</div>
            <div class="col-name">Имя</div>
            <div class="col-email">Email</div>
            <div class="col-ranks">Роли</div>
            <div class="col-stats">Стат.</div>
            <div class="col-actions">Действия</div>
          </div>
          
          <div v-for="user in users" :key="user.id" class="table-row">
            <div class="col-id">{{ user.id }}</div>
            <div class="col-name">{{ user.name }}</div>
            <div class="col-email">{{ user.email }}</div>
            <div class="col-ranks">
              <span v-for="(rank, idx) in user.ranks" :key="idx" class="rank-badge">
                {{ rank.rank }}
                <span v-if="rank.expires_at" class="expires">
                  (до {{ formatDate(rank.expires_at) }})
                </span>
              </span>
            </div>
            <div class="col-stats">
              <button @click="loadUserStats(user.id)" class="stats-btn">📊</button>
            </div>
            <div class="col-actions">
              <button @click="manageRanks(user)" class="manage-ranks-btn">Ранги</button>
              <button 
                @click="deleteUser(user.id)" 
                class="delete-btn"
                :disabled="user.id === currentUserId"
                title="Удалить пользователя"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 512 512">
                  <g>
                    <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                  </g>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Содержимое вкладки Настройки ИИ -->
    <div v-else-if="activeTab === 'ai'" class="tab-content">
      <div class="admin-actions">
        <button @click="loadAiData" class="refresh-btn">Обновить</button>
      </div>

      <!-- Секция API ключей -->
      <div class="ai-section">
        <h4>API Ключи</h4>
        <div class="add-key-form">
          <h5>Добавить новый API ключ</h5>
          <div class="form-row">
            <select v-model="newKeyForm.preset" class="form-select">
              <option value="custom">Кастомный</option>
              <option value="google">Google (Gemini)</option>
              <option value="openai">OpenAI</option>
              <option value="yandex">Yandex</option>
              <option value="gigachat">Gigachat</option>
              <option value="deepseek">DeepSeek</option>
            </select>
            <input 
              v-model="newKeyForm.key" 
              type="password" 
              placeholder="API ключ"
              class="form-input"
            />
            <input 
              v-if="newKeyForm.preset === 'custom'"
              v-model="newKeyForm.provider_url" 
              type="text" 
              placeholder="URL провайдера"
              class="form-input"
            />
            <button @click="createAiKey" class="add-btn">Добавить</button>
          </div>
        </div>

        <div v-if="aiKeys.length === 0" class="no-data">
          Нет API ключей
        </div>
        
        <div v-else class="ai-keys-list">
          <div v-for="key in aiKeys" :key="key.id" class="ai-key-card">
            <div class="key-header">
              <span class="provider">{{ key.provider_url }}</span>
              <span class="key-preview">{{ key.key }}</span>
              <button @click="deleteAiKey(key.id)" class="delete-btn small" title="Удалить API ключ">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 512 512">
                  <g>
                    <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                  </g>
                </svg>
              </button>
            </div>
            <div class="models-list">
              <div class="models-header">
                <h5>Модели:</h5>
                <button
                  class="model-add-btn"
                  type="button"
                  @click="openAddModelForKey(key.id)"
                  title="Добавить модель"
                >
                  +
                </button>
              </div>

              <!-- Строка добавления модели для выбранного ключа -->
              <div
                v-if="newModelForm.keyId === key.id"
                class="model-item model-item-edit"
              >
                <input
                  v-model="newModelForm.model_name"
                  type="text"
                  placeholder="Название модели (например, gpt-4o)"
                  class="form-input"
                />
                <input
                  v-model.number="newModelForm.priority"
                  type="number"
                  min="1"
                  max="10"
                  placeholder="Приоритет"
                  class="form-input"
                  style="max-width: 100px"
                />
                <button
                  type="button"
                  class="save-btn"
                  @click="addSystemModel(key.id)"
                >
                  ✓
                </button>
                <button
                  type="button"
                  class="cancel-btn"
                  @click="newModelForm.keyId = null"
                >
                  ✗
                </button>
              </div>

              <!-- Список существующих моделей -->
              <div
                v-for="model in key.models"
                :key="model.id"
                class="model-item"
              >
                <div v-if="editingModelId === model.id" class="model-edit-row">
                  <input
                    v-model="editModelForm.model_name"
                    type="text"
                    class="form-input"
                    style="flex: 2"
                  />
                  <input
                    v-model.number="editModelForm.priority"
                    type="number"
                    min="1"
                    max="10"
                    class="form-input"
                    style="max-width: 80px"
                  />
                  <button
                    type="button"
                    class="save-btn"
                    @click="saveModel(model.id)"
                  >
                    ✓
                  </button>
                  <button
                    type="button"
                    class="cancel-btn"
                    @click="cancelEditModel"
                  >
                    ✗
                  </button>
                </div>
                <div v-else class="model-view-row">
                  <div class="model-main">
                    <span class="model-name">{{ model.model_name }}</span>
                    <span class="model-priority">Приоритет: {{ model.priority }}</span>
                  </div>
                  <div class="model-actions">
                    <label class="toggle-switch">
                      <input 
                        type="checkbox" 
                        :checked="model.works" 
                        @change="toggleModel(model.id)"
                      />
                      <span class="toggle-slider"></span>
                    </label>
                    <button
                      type="button"
                      class="edit-btn small"
                      @click="startEditModel(model)"
                      title="Редактировать модель"
                    >
                      ✎
                    </button>
                    <button
                      type="button"
                      class="delete-btn small"
                      @click="deleteModel(model.id)"
                      title="Удалить модель"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 512 512">
                        <g>
                          <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                        </g>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Секция конфигураций ИИ -->
      <div class="ai-section">
        <h4>Конфигурации ИИ</h4>
        <div class="add-config-form" v-if="showAddConfig">
          <h5>Добавить новую конфигурацию</h5>
          <div class="form-group">
            <label>Имя конфигурации</label>
            <input v-model="newConfigForm.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>System Instruction</label>
            <textarea v-model="newConfigForm.system_instruction" class="form-textarea" rows="4"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Temperature (0.0 - 1.0)</label>
              <input v-model.number="newConfigForm.temperature" type="number" step="0.1" min="0" max="1" class="form-input" />
            </div>
            <div class="form-group">
              <label>
                <input v-model="newConfigForm.is_stream" type="checkbox" />
                Stream
              </label>
            </div>
            <div class="form-group">
              <label>
                <input v-model="newConfigForm.is_json" type="checkbox" />
                JSON
              </label>
            </div>
          </div>
          <div class="form-actions">
            <button @click="createAiConfig" class="save-btn">Сохранить</button>
            <button @click="showAddConfig = false" class="cancel-btn">Отмена</button>
          </div>
        </div>

        <button v-else @click="showAddConfig = true" class="add-config-btn">+ Добавить конфигурацию</button>

        <div v-if="aiConfigs.length === 0" class="no-data">
          Нет конфигураций
        </div>
        
        <div v-else class="ai-configs-list">
          <div v-for="config in aiConfigs" :key="config.id" class="ai-config-card">
            <div class="config-header">
              <h5>{{ config.name }}</h5>
              <div class="config-actions">
                <button @click="startEditConfig(config)" class="edit-btn small">✎</button>
                <button @click="deleteAiConfig(config.id)" class="delete-btn small" title="Удалить конфигурацию">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 512 512">
                    <g>
                      <path d="M 123.20 510.55 C105.11,506.17 91.63,490.76 89.07,471.50 C88.48,467.10 86.43,444.15 84.50,420.50 C76.32,319.81 61.96,147.64 61.74,147.53 C61.61,147.47 59.04,146.31 56.04,144.96 C39.80,137.65 29.07,117.65 31.67,99.58 C34.54,79.64 49.40,64.12 68.61,60.98 C71.85,60.45 91.71,60.01 112.75,60.01 L 151.00 60.00 L 151.00 51.14 C151.00,46.26 151.46,39.85 152.02,36.89 C155.43,18.93 169.93,4.43 187.89,1.02 C195.14,-0.35 316.86,-0.35 324.11,1.02 C342.07,4.43 356.57,18.93 359.98,36.89 C360.54,39.85 361.00,46.26 361.00,51.14 L 361.00 60.00 L 399.25 60.01 C420.29,60.01 440.15,60.45 443.39,60.98 C462.60,64.12 477.46,79.64 480.33,99.58 C482.93,117.65 472.94,136.45 456.26,144.87 L 450.21 147.93 L 449.58 153.71 C448.99,159.14 435.26,325.00 427.50,420.50 C425.57,444.15 423.52,467.10 422.93,471.50 C420.29,491.29 406.05,507.00 387.20,510.90 C379.00,512.60 130.29,512.26 123.20,510.55 ZM 386.68 479.40 C393.41,474.38 391.93,488.58 414.47,212.50 C416.94,182.25 419.15,155.81 419.39,153.75 L 419.81 150.00 L 256.00 150.00 L 92.19 150.00 L 92.61 153.75 C92.85,155.81 95.06,182.25 97.53,212.50 C113.77,411.39 118.98,471.06 120.35,473.72 C122.11,477.12 124.73,479.57 128.02,480.89 C129.63,481.54 175.00,481.82 257.18,481.69 L 383.85 481.50 L 386.68 479.40 ZM 443.40 117.73 C453.45,111.97 453.23,97.87 443.00,92.12 L 439.23 90.00 L 256.00 90.00 L 72.77 90.00 L 69.00 92.12 C58.77,97.87 58.55,111.97 68.60,117.73 L 72.50 119.97 L 256.00 119.97 L 439.50 119.97 L 443.40 117.73 ZM 331.00 51.52 C331.00,40.41 329.19,35.78 323.54,32.47 L 319.32 30.00 L 256.00 30.00 L 192.68 30.00 L 188.46 32.47 C182.81,35.78 181.00,40.41 181.00,51.52 L 181.00 60.00 L 256.00 60.00 L 331.00 60.00 L 331.00 51.52 ZM 173.42 449.54 C170.83,447.98 168.74,445.71 167.69,443.30 C166.35,440.21 164.63,416.57 158.46,316.54 C151.24,199.35 150.96,193.39 152.52,189.31 C155.64,181.13 164.79,177.81 172.85,181.93 C181.07,186.12 180.07,177.57 188.58,315.67 L 196.17 438.83 L 194.17 443.35 C190.58,451.46 181.26,454.23 173.42,449.54 ZM 248.86 449.84 C246.86,448.68 244.27,446.04 243.11,443.98 L 241.00 440.23 L 241.00 316.00 L 241.00 191.77 L 243.12 188.00 C245.59,183.61 251.40,180.00 256.00,180.00 C260.60,180.00 266.41,183.61 268.88,188.00 L 271.00 191.77 L 271.00 316.00 L 271.00 440.23 L 268.88,444.00 C266.38,448.45 260.57,452.01 255.86,451.98 C254.01,451.96 250.86,451.00 248.86,449.84 ZM 323.66 449.89 C320.93,448.45 319.25,446.56 317.83,443.35 L 315.83 438.83 L 323.42 315.67 C332.00,176.43 330.88,185.71 339.67,181.82 C348.11,178.09 356.39,181.22 359.48,189.31 C361.04,193.39 360.76,199.36 353.55,316.54 C345.10,454.02 346.04,445.90 338.07,449.96 C333.07,452.51 328.60,452.49 323.66,449.89 Z" fill="rgba(0,0,0,1)"/>
                    </g>
                  </svg>
                </button>
              </div>
            </div>
            <div class="config-body">
              <div class="form-group">
                <label>System Instruction</label>
                <textarea 
                  v-if="editingConfigId === config.id"
                  v-model="editConfigForm.system_instruction" 
                  class="form-textarea" 
                  rows="4"
                ></textarea>
                <p v-else class="config-text">{{ config.system_instruction }}</p>
              </div>
              <div class="config-params">
                <div class="param">
                  <span class="param-label">Temperature:</span>
                  <input 
                    v-if="editingConfigId === config.id"
                    v-model.number="editConfigForm.temperature" 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="1" 
                    class="param-input"
                  />
                  <span v-else>{{ config.temperature }}</span>
                </div>
                <div class="param">
                  <span class="param-label">Stream:</span>
                  <input 
                    v-if="editingConfigId === config.id"
                    v-model="editConfigForm.is_stream" 
                    type="checkbox"
                  />
                  <span v-else>{{ config.is_stream ? '✓' : '✗' }}</span>
                </div>
                <div class="param">
                  <span class="param-label">JSON:</span>
                  <input 
                    v-if="editingConfigId === config.id"
                    v-model="editConfigForm.is_json" 
                    type="checkbox"
                  />
                  <span v-else>{{ config.is_json ? '✓' : '✗' }}</span>
                </div>
              </div>
            </div>
            <div class="config-footer" v-if="editingConfigId === config.id">
              <button @click="saveConfig(config.id)" class="save-btn">Сохранить</button>
              <button @click="cancelEditConfig" class="cancel-btn">Отмена</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import auth from '@/auth'

const activeTab = ref('metrics')
const isLoading = ref(false)
const error = ref(null)

// Данные метрик
const metrics = ref([])
const editingMetricId = ref(null)
const editMetricForm = ref({ name: '', description: '', weight: 1.0 })

// Данные пользователей
const users = ref([])
const currentUserId = ref(null)
const searchQuery = ref('')
const allRanks = ref([])
const selectedUserRanks = ref(null) // null = не выбран, [] = выбранный список рангов
const selectedUserStats = ref(null) // { analysis: 0, chat: 0 }
const selectedUserName = ref('')
const newRankName = ref('')
const newWorkerForm = ref({
  email: '',
  password: '',
  name: ''
})

// Данные ИИ
const aiConfigs = ref([])
const aiKeys = ref([])
const showAddConfig = ref(false)
const newConfigForm = ref({
  name: '',
  system_instruction: '',
  temperature: 0.7,
  is_stream: false,
  is_json: true
})
const editingConfigId = ref(null)
const editConfigForm = ref({
  system_instruction: '',
  temperature: 0.7,
  is_stream: false,
  is_json: true
})
const newKeyForm = ref({
  preset: 'custom',
  key: '',
  provider_url: ''
})
const newModelForm = ref({
  keyId: null,
  model_name: '',
  priority: 1
})
const editingModelId = ref(null)
const editModelForm = ref({
  model_name: '',
  priority: 1
})

// Загрузка метрик
const loadMetrics = async () => {
  try {
    isLoading.value = true
    error.value = null
    const res = await api.get('/admin/metrics')
    // сортируем метрики по id по возрастанию для стабильного отображения
    metrics.value = [...res.data].sort((a, b) => (a.id || 0) - (b.id || 0))
  } catch (e) {
    console.error('Ошибка загрузки метрик', e)
    error.value = e.response?.data?.detail || 'Ошибка загрузки метрик'
  } finally {
    isLoading.value = false
  }
}

// Загрузка пользователей
const loadUsers = async () => {
  try {
    isLoading.value = true
    error.value = null
    const res = await api.get('/admin/users')
    users.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки пользователей', e)
    error.value = e.response?.data?.detail || 'Ошибка загрузки пользователей'
  } finally {
    isLoading.value = false
  }
}

// Загрузка рангов
const loadRanks = async () => {
  try {
    const res = await api.get('/admin/ranks')
    allRanks.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки рангов', e)
  }
}

// Поиск пользователей
const searchUsers = async () => {
  if (!searchQuery.value.trim()) return
  
  try {
    isLoading.value = true
    error.value = null
    const res = await api.get('/admin/users/search', { params: { email: searchQuery.value } })
    users.value = res.data
  } catch (e) {
    console.error('Ошибка поиска пользователей', e)
    const detail = e.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Ошибка поиска'
  } finally {
    isLoading.value = false
  }
}

// Загрузка статистики пользователя
const loadUserStats = async (userId) => {
  try {
    const res = await api.get(`/admin/users/${userId}/usage`)
    selectedUserStats.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки статистики', e)
    alert('Не удалось загрузить статистику')
  }
}

// Загрузка рангов пользователя
const manageRanks = async (user) => {
  selectedUserName.value = user.name
  selectedUserRanks.value = user.ranks
  selectedUserStats.value = null
}

// Назначение ранга
const assignRank = async () => {
  if (!newRankName.value || selectedUserRanks.value === null) return
  
  try {
    const userId = users.value.find(u => u.name === selectedUserName.value)?.id
    if (!userId) {
      alert('Пользователь не найден')
      return
    }
    
    await api.post(`/admin/users/${userId}/ranks/${newRankName.value}`)
    newRankName.value = ''
    await loadUsers() // Обновляем список пользователей
    // Обновляем выбранные ранги
    const updatedUser = users.value.find(u => u.id === userId)
    if (updatedUser) {
      selectedUserRanks.value = updatedUser.ranks
    }
  } catch (e) {
    console.error('Ошибка назначения ранга', e)
    alert('Не удалось назначить ранг: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Удаление ранга
const removeRank = async (rankName) => {
  if (!confirm(`Удалить ранг "${rankName}" у пользователя?`)) return
  
  try {
    const userId = users.value.find(u => u.name === selectedUserName.value)?.id
    if (!userId) {
      alert('Пользователь не найден')
      return
    }
    
    await api.delete(`/admin/users/${userId}/ranks/${rankName}`)
    await loadUsers()
    // Обновляем выбранные ранги
    const updatedUser = users.value.find(u => u.id === userId)
    if (updatedUser) {
      selectedUserRanks.value = updatedUser.ranks
    }
  } catch (e) {
    console.error('Ошибка удаления ранга', e)
    alert('Не удалось удалить ранг: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Создание воркера
const createWorker = async () => {
  if (!newWorkerForm.value.email || !newWorkerForm.value.password || !newWorkerForm.value.name) {
    alert('Заполните все поля')
    return
  }
  
  try {
    await api.post('/admin/users/worker', {
      email: newWorkerForm.value.email,
      password: newWorkerForm.value.password,
      name: newWorkerForm.value.name
    })
    newWorkerForm.value = { email: '', password: '', name: '' }
    await loadUsers()
    alert('Воркер успешно создан')
  } catch (e) {
    console.error('Ошибка создания воркера', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось создать воркера: ' + msg)
  }
}

// Загрузка данных ИИ
const loadAiData = async () => {
  try {
    isLoading.value = true
    error.value = null
    const [configsRes, keysRes] = await Promise.all([
      api.get('/admin/ai-configs'),
      api.get('/admin/ai-keys')
    ])
    aiConfigs.value = configsRes.data
    aiKeys.value = keysRes.data
  } catch (e) {
    console.error('Ошибка загрузки данных ИИ', e)
    error.value = e.response?.data?.detail || 'Ошибка загрузки данных ИИ'
  } finally {
    isLoading.value = false
  }
}

// Редактирование метрик
const startEditMetric = (metric) => {
  editingMetricId.value = metric.id
  editMetricForm.value = {
    name: metric.name,
    description: metric.description || '',
    weight: metric.weight
  }
}

const cancelEditMetric = () => {
  editingMetricId.value = null
  editMetricForm.value = { name: '', description: '', weight: 1.0 }
}

const saveMetric = async (metricId) => {
  try {
    await api.patch(`/admin/metrics/${metricId}`, editMetricForm.value)
    await loadMetrics()
    editingMetricId.value = null
  } catch (e) {
    console.error('Ошибка сохранения метрики', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось сохранить: ' + msg)
  }
}

const deleteMetric = async (metricId) => {
  if (!confirm('Удалить эту метрику?')) return
  
  try {
    await api.delete(`/admin/metrics/${metricId}`)
    await loadMetrics()
  } catch (e) {
    console.error('Ошибка удаления метрики', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось удалить: ' + msg)
  }
}

// Удаление пользователя
const deleteUser = async (userId) => {
  if (!confirm('Удалить этого пользователя?')) return
  
  try {
    await api.delete(`/admin/users/${userId}`)
    await loadUsers()
    selectedUserRanks.value = null
    selectedUserStats.value = null
  } catch (e) {
    console.error('Ошибка удаления пользователя', e)
    alert('Не удалось удалить: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Управление AI конфигурациями
const createAiConfig = async () => {
  try {
    await api.post('/admin/ai-configs', newConfigForm.value)
    showAddConfig.value = false
    newConfigForm.value = {
      name: '',
      system_instruction: '',
      temperature: 0.7,
      is_stream: false,
      is_json: true
    }
    await loadAiData()
  } catch (e) {
    console.error('Ошибка создания конфигурации', e)
    alert('Не удалось создать: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

const startEditConfig = (config) => {
  editingConfigId.value = config.id
  editConfigForm.value = {
    system_instruction: config.system_instruction,
    temperature: config.temperature,
    is_stream: config.is_stream,
    is_json: config.is_json
  }
}

const cancelEditConfig = () => {
  editingConfigId.value = null
  editConfigForm.value = {
    system_instruction: '',
    temperature: 0.7,
    is_stream: false,
    is_json: true
  }
}

const saveConfig = async (configId) => {
  try {
    await api.put(`/admin/ai-configs/${configId}`, editConfigForm.value)
    editingConfigId.value = null
    await loadAiData()
  } catch (e) {
    console.error('Ошибка сохранения конфигурации', e)
    alert('Не удалось сохранить: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

const deleteAiConfig = async (configId) => {
  if (!confirm('Удалить эту конфигурацию?')) return
  
  try {
    await api.delete(`/admin/ai-configs/${configId}`)
    await loadAiData()
  } catch (e) {
    console.error('Ошибка удаления конфигурации', e)
    alert('Не удалось удалить: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Управление API ключами
const createAiKey = async () => {
  try {
    await api.post('/admin/ai-keys', {
      preset: newKeyForm.value.preset,
      key: newKeyForm.value.key,
      provider_url: newKeyForm.value.provider_url || undefined
    })
    newKeyForm.value = {
      preset: 'custom',
      key: '',
      provider_url: ''
    }
    await loadAiData()
  } catch (e) {
    console.error('Ошибка создания ключа', e)
    alert('Не удалось создать ключ: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Открыть форму добавления модели для конкретного ключа
const openAddModelForKey = (keyId) => {
  newModelForm.value.keyId = keyId
  newModelForm.value.model_name = ''
  newModelForm.value.priority = 1
}

// Добавление модели к существующему системному ключу
const addSystemModel = async (keyId) => {
  const targetKeyId = keyId || newModelForm.value.keyId
  if (!targetKeyId || !newModelForm.value.model_name.trim()) {
    alert('Укажите имя модели')
    return
  }

  try {
    await api.post(`/admin/ai-keys/${targetKeyId}/models`, {
      model_name: newModelForm.value.model_name.trim(),
      priority: newModelForm.value.priority || 1
    })
    newModelForm.value.model_name = ''
    newModelForm.value.priority = 1
    await loadAiData()
  } catch (e) {
    console.error('Ошибка добавления модели', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось добавить модель: ' + msg)
  }
}

// Редактирование модели
const startEditModel = (model) => {
  editingModelId.value = model.id
  editModelForm.value = {
    model_name: model.model_name,
    priority: model.priority
  }
}

const cancelEditModel = () => {
  editingModelId.value = null
  editModelForm.value = {
    model_name: '',
    priority: 1
  }
}

const saveModel = async (modelId) => {
  try {
    await api.patch(`/admin/ai-models/${modelId}`, {
      model_name: editModelForm.value.model_name.trim(),
      priority: editModelForm.value.priority
    })
    editingModelId.value = null
    await loadAiData()
  } catch (e) {
    console.error('Ошибка обновления модели', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось сохранить модель: ' + msg)
  }
}

const deleteModel = async (modelId) => {
  if (!confirm('Удалить эту модель?')) return

  try {
    await api.delete(`/admin/ai-models/${modelId}`)
    if (editingModelId.value === modelId) {
      editingModelId.value = null
    }
    await loadAiData()
  } catch (e) {
    console.error('Ошибка удаления модели', e)
    const detail = e.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Ошибка'
    alert('Не удалось удалить модель: ' + msg)
  }
}

const deleteAiKey = async (keyId) => {
  if (!confirm('Удалить этот API ключ и все связанные модели?')) return
  
  try {
    await api.delete(`/admin/ai-keys/${keyId}`)
    await loadAiData()
  } catch (e) {
    console.error('Ошибка удаления ключа', e)
    alert('Не удалось удалить: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

const toggleModel = async (modelId) => {
  try {
    await api.patch(`/admin/ai-models/${modelId}/toggle`)
    await loadAiData()
  } catch (e) {
    console.error('Ошибка переключения модели', e)
    alert('Не удалось изменить состояние: ' + (e.response?.data?.detail || 'Ошибка'))
  }
}

// Форматирование даты
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU')
}

// Повторная загрузка
const retryLoad = () => {
  if (activeTab.value === 'metrics') {
    loadMetrics()
  } else if (activeTab.value === 'users') {
    loadUsers()
  } else {
    loadAiData()
  }
}

onMounted(async () => {
  try {
    // Подгружаем текущего пользователя
    const user = await auth.getCurrentUser()
    currentUserId.value = user?.id || null
  } catch (e) {
    console.error('Ошибка получения текущего пользователя', e)
  }

  // При первом открытии панели сразу подгружаем данные для всех вкладок,
  // чтобы не требовать нажатия на "Обновить"
  isLoading.value = true
  error.value = null
  try {
    await Promise.all([
      loadMetrics(),
      loadUsers(),
      loadAiData(),
      loadRanks()
    ])
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.admin-block {
  margin-top: 20px;
}

.admin-block h3 {
  margin-bottom: 16px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: #f0f0f0;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: #e0e0e0;
}

.tab-btn.active {
  background: #007bff;
  color: white;
}

/* Адаптивность для вкладок на мобильных */
@media (max-width: 480px) {
  .tabs {
    gap: 4px;
    display: grid;
  }
  
  .tab-btn {
    padding: 6px 12px;
    font-size: 0.85em;
  }
}

.admin-loading, .admin-error {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.admin-loading .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

.admin-error button {
  margin-top: 10px;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.admin-actions {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.refresh-btn {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #5a6268;
}

.no-data {
  text-align: center;
  padding: 30px;
  color: #666;
  font-style: italic;
}

/* Таблицы - адаптивность с горизонтальным скроллом на мобильных */
.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.metrics-table, .users-table {
  min-width: 600px;
}

.table-header {
  display: grid;
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.table-row {
  display: grid;
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
}

.table-row:last-child {
  border-bottom: none;
}

.table-header > div, .table-row > div {
  padding: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Колонки для метрик */
.metrics-table .table-header {
  grid-template-columns: 50px 1fr 1fr 80px 100px;
}

.metrics-table .table-row {
  grid-template-columns: 50px 1fr 1fr 80px 100px;
}

/* Колонки для пользователей */
.users-table .table-header {
  grid-template-columns: 50px 1fr 1.2fr 150px 60px 100px;
}

.users-table .table-row {
  grid-template-columns: 50px 1fr 1.2fr 150px 60px 100px;
}

.col-actions {
  display: flex;
  gap: 6px;
}

.edit-btn, .save-btn, .cancel-btn, .delete-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.edit-btn {
  background: #ffc107;
  color: #000;
}

.save-btn {
  background: #28a745;
  color: white;
}

.cancel-btn {
  background: #dc3545;
  color: white;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn.small {
  padding: 2px 8px;
  font-size: 0.8em;
}

.delete-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.edit-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #007bff;
  border-radius: 4px;
  font-size: 0.9em;
}

.edit-input:focus {
  outline: none;
  border-color: #0056b3;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.rank-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #e9ecef;
  border-radius: 12px;
  font-size: 0.85em;
  margin-right: 6px;
  margin-bottom: 4px;
}

.rank-badge .expires {
  color: #666;
  font-size: 0.8em;
}

/* Forms */
.form-input, .form-select, .form-textarea {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95em;
  flex: 2 1 0%;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.form-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9em;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.add-btn, .add-config-btn, .add-rank-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95em;
}

.add-btn:hover, .add-config-btn:hover, .add-rank-btn:hover {
  background: #218838;
}

.add-config-btn {
  background: #17a2b8;
  margin-bottom: 20px;
}

.add-config-btn:hover {
  background: #138496;
}

/* User Management */
.create-worker-form, .search-users {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
}

.create-worker-form h4, .search-users h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #333;
}

.search-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95em;
}

.search-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.search-btn:hover {
  background: #0056b3;
}

/* Адаптивность для поиска на мобильных */
@media (max-width: 480px) {
  .search-row {
    flex-direction: column;
  }
  
  .search-input {
    min-width: 100%;
  }
  
  .search-btn {
    width: 100%;
  }
}

.user-stats-card, .user-ranks-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
}

.user-stats-card h4, .user-ranks-card h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #333;
}

.stats-grid {
  display: flex;
  gap: 30px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-weight: 500;
  color: #555;
}

.stat-value {
  font-size: 1.5em;
  font-weight: 600;
  color: #007bff;
}

.close-stats-btn, .close-ranks-btn {
  margin-top: 12px;
  padding: 6px 12px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.close-stats-btn:hover, .close-ranks-btn:hover {
  background: #5a6268;
}

.ranks-current {
  margin-bottom: 16px;
}

.ranks-current h5 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #555;
}

.no-ranks {
  color: #666;
  font-style: italic;
  padding: 8px;
}

.ranks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.rank-name {
  font-weight: 500;
  color: #333;
}

.rank-expires {
  color: #666;
  font-size: 0.9em;
}

.remove-rank-btn {
  margin-left: auto;
  padding: 4px 8px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
}

.remove-rank-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.add-rank-form {
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.add-rank-form h5 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #555;
}

.add-rank-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.add-rank-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.manage-ranks-btn {
  padding: 4px 8px;
  background: #ffc107;
  color: #000;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
}

.stats-btn {
  padding: 4px 8px;
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
}

/* AI Settings Styles */
.ai-section {
  margin-bottom: 30px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
  max-height: 600px;
  overflow-y: auto;
}

.ai-section h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
}

.ai-section h5 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #555;
  font-size: 1em;
}

.add-key-form, .add-config-form {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
}

.ai-keys-list, .ai-configs-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-key-card, .ai-config-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
}

.key-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.provider {
  font-weight: 600;
  color: #333;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.key-preview {
  font-family: monospace;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.models-list h5 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #555;
}

.model-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  /* justify-content: space-between; */
  gap: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 6px;
}

.model-main {
  display: flex;
  flex-direction: row;
  gap: 12px;
  align-items: center;
}

.model-name {
  font-weight: 500;
  color: #333;
}

.model-priority {
  color: #666;
  font-size: 0.9em;
}

.model-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-edit-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  width: 100%;
  flex-wrap: wrap;
}

/* .model-edit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 6px;
} */

.model-item-edit {
  margin-bottom: 8px;
}

/* Адаптивность для редактирования модели на мобильных */
@media (max-width: 480px) {
  .model-item-edit{
    flex-direction: column;
    align-items: stretch;
  }

  .model-item-edit button, input {
    max-width: 100%;
  }

  .model-edit-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .model-edit-row .form-input {
    width: 100%;
  }
  
  .model-edit-row .form-input[style*="max-width"] {
    max-width: 100% !important;
  }
}

.models-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.models-header h5 {
  margin: 0;
}

.model-add-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: #28a745;
  color: #fff;
  font-size: 20px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease;
}

.model-add-btn:hover {
  background: #218838;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  margin-left: auto;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .toggle-slider {
  background-color: #28a745;
}

input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

/* Config Card */
.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.config-header h5 {
  margin: 0;
  color: #333;
}

.config-actions {
  display: flex;
  gap: 6px;
}

.config-body {
  margin-bottom: 12px;
}

.config-text {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  font-size: 0.9em;
  line-height: 1.5;
  margin: 0;
}

.config-params {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.param {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-label {
  font-weight: 500;
  color: #555;
}

.param-input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.config-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>






